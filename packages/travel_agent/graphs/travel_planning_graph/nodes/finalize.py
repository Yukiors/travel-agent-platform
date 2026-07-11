"""Node for finalizing and confirming the travel plan."""

import json
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.prompts import FINALIZE_SYSTEM_PROMPT, FINALIZE_USER_TEMPLATE
from travel_agent.llm.structured import StructuredOutputError, invoke_structured_json
from travel_agent.schemas import FinalizedPlan


async def finalize_plan(state: TravelPlanningState) -> dict:
    """审核优化行程，生成最终确认的旅行计划。

    对已生成的行程进行合理性检查，包括时间冲突、预算分析、逻辑连贯性等。
    生成友好的行程摘要、亮点提炼和实用建议，提供完整的旅行计划确认。

    Args:
        state: 旅行规划状态对象，包含目的地、日期、预算、已生成的行程等信息

    Returns:
        包含以下字段的字典：
        - messages: AIMessage 列表，包含最终确认的行程摘要
        - final_plan: 最终确认的计划数据（包含摘要、亮点、建议、预算分析）
        - next_step: 空字符串（流程终止）

    处理流程：
        1. 从 state 提取基本信息和已生成的行程
        2. 计算旅行天数
        3. 将行程数据格式化为易读的字符串
        4. 使用 LLM 审核行程并生成最终确认结果（JSON 格式）
        5. 清洗 LLM 返回的 JSON 字符串（去除 markdown 代码块）
        6. 解析 JSON 并返回结果，如果解析失败则返回错误信息
    """
    # 从状态对象中提取旅行相关信息
    destination = state.destination
    start_date = state.start_date
    end_date = state.end_date
    budget = state.budget or 0.0
    num_travelers = state.num_travelers
    itinerary = state.itinerary

    # 计算旅行天数
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return {
            "messages": [AIMessage(content="日期格式有误，请重新输入。")],
            "next_step": "",
        }
    num_days = (end - start).days + 1

    # 将行程数据格式化为易读的字符串，便于 LLM 理解和审核
    itinerary_str = json.dumps(itinerary, ensure_ascii=False, indent=2) if itinerary else "暂无行程数据"

    # 组装提示词：SystemMessage 定义角色和输出格式，HumanMessage 包含行程数据
    prompt = [
        SystemMessage(content=FINALIZE_SYSTEM_PROMPT),
        HumanMessage(
            content=FINALIZE_USER_TEMPLATE.format(destination=destination, start_date=start_date, end_date=end_date,
                                                  num_days=num_days, num_travelers=num_travelers, budget=budget,
                                                  itinerary=itinerary_str))
    ]

    # 获取 LLM 实例并调用生成最终确认
    llm = get_llm(fast=True)
    try:
        final_plan = invoke_structured_json(
            llm=llm,
            schema=FinalizedPlan,
            messages=prompt,
        )
        # model_dump(mode="json") 将 Pydantic 模型转为 JSON-safe dict，
        # 与 TravelPlanningState 的 final_plan: dict 类型兼容。
        return {
            "messages": [AIMessage(content=final_plan.summary or "旅行计划已确认")],
            "final_plan": final_plan.model_dump(mode="json"),
            "next_step": "",
        }
    except StructuredOutputError:
        # JSON 解析失败——LLM 返回格式不符合预期。
        # 返回通用错误消息并以 next_step="" 终止 graph，
        # 避免将无效数据传播到下游节点。
        return {
            "messages": [AIMessage(content="处理您的请求时遇到问题，请稍后重试。")],
            "next_step": "",
        }
