"""Node for finalizing and confirming the travel plan."""

import json
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.prompts import FINALIZE_SYSTEM_PROMPT, FINALIZE_USER_TEMPLATE


def _clean_json_response(raw: str) -> str:
    """清洗 LLM 返回的原始字符串，去除 markdown 代码块包裹和首尾空白。

    LLM 经常不按指令直接输出裸 JSON，而是用 markdown 代码块包裹，
    如 ```json ... ``` 或 ``` ... ```。本函数负责将这些包裹剥掉，
    返回纯 JSON 字符串供 json.loads 解析。

    Args:
        raw: LLM 返回的原始字符串，可能包含 markdown 代码块。

    Returns:
        去除代码块标记和首尾空白后的纯 JSON 字符串。

    处理示例:
        "```json\\n{\"a\": 1}\\n```" → "{\"a\": 1}"
        "  \\n```\\n{\"a\": 1}\\n```\\n  " → "{\"a\": 1}"
        "{\"a\": 1}" → "{\"a\": 1}"
    """
    # 先做一次 strip，去掉首尾空白和换行
    raw = raw.strip()

    # 检查是否以 ``` 开头（兼容 ``` 和 ```json 两种写法）
    if raw.startswith("```"):
        # 找到第一个换行符的位置，跳过整个 fence 行
        first_newline = raw.find("\n")
        if first_newline != -1:
            raw = raw[first_newline + 1:]

        # 去掉末尾的 ```（可能在最后一行或紧贴内容）
        if raw.endswith("```"):
            raw = raw[:-3]

    # 再次 strip，去除 fence 行剥离后可能残留的空白
    return raw.strip()


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
        HumanMessage(content=FINALIZE_USER_TEMPLATE.format(destination=destination, start_date=start_date, end_date=end_date, num_days=num_days, num_travelers=num_travelers, budget=budget, itinerary=itinerary_str))
    ]

    # 获取 LLM 实例并调用生成最终确认
    llm = get_llm(fast=True)
    try:
        response = await llm.ainvoke(prompt)
    except Exception:
        return {
            "messages": [AIMessage(content="服务暂时不可用，请稍后重试。")],
            "next_step": "",
        }
    # 清洗返回内容，去除可能存在的 markdown 代码块包裹
    json_str = _clean_json_response(str(response.content))

    try:
        # 尝试解析 JSON 字符串为 Python 对象
        final_plan = json.loads(json_str)
        return {
            "messages": [AIMessage(content=final_plan.get("summary", "旅行计划已确认"))],
            "final_plan": final_plan,
            "next_step": "",
        }
    except json.JSONDecodeError:
        # JSON 解析失败，返回错误提示并终止流程
        return {
            "messages": [AIMessage(content="处理您的请求时遇到问题，请稍后重试。")],
            "next_step": "",
        }
