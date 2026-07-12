"""Node for building the final travel itinerary."""

import json
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.prompts import ITINERARY_SYSTEM_PROMPT, ITINERARY_USER_TEMPLATE
from travel_agent.llm.structured import StructuredOutputError, invoke_structured_json
from travel_agent.schemas import ItineraryResult


async def build_itinerary(state: TravelPlanningState) -> dict:
    """根据搜索结果生成结构化的每日行程计划。

    使用 LLM 将航班、酒店、景点数据整合成按天分组的完整旅行计划。
    返回的行程包含每日活动安排、时间、地点、费用等详细信息。

    Args:
        state: 旅行规划状态对象，包含目的地、日期、预算、航班、酒店、景点等信息

    Returns:
        包含以下字段的字典：
        - messages: AIMessage 列表，包含行程生成完成的提示信息
        - itinerary: 按天分组的行程数据（JSON 数组格式）
        - next_step: 下一个要执行的节点名称（"finalize_plan" 或空字符串表示终止）

    处理流程：
        1. 从 state 提取所有旅行相关信息（偏好、航班、酒店、景点）
        2. 计算旅行天数
        3. 将航班、酒店、景点数据格式化为易读的字符串
        4. 使用 LLM 生成按天分组的完整行程（JSON 格式）
        5. 清洗 LLM 返回的 JSON 字符串（去除 markdown 代码块）
        6. 解析 JSON 并返回结果，如果解析失败则返回错误信息并终止流程
    """
    # 从状态对象中提取旅行相关信息
    destination = state.destination
    start_date = state.start_date
    end_date = state.end_date
    budget = state.budget or 0.0
    num_travelers = state.num_travelers
    interests = state.interests
    flights = state.flights
    hotels = state.hotels
    attractions = state.attractions

    # 计算旅行天数，用于生成对应天数的行程安排
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return {
            "messages": [AIMessage(content="日期格式有误，请重新输入。")],
            "next_step": "",
        }
    num_days = (end - start).days + 1

    # 将航班、酒店、景点数据格式化为易读的字符串，便于 LLM 理解
    flights_str = json.dumps(flights, ensure_ascii=False, indent=2) if flights else "暂无航班数据"
    hotels_str = json.dumps(hotels, ensure_ascii=False, indent=2) if hotels else "暂无酒店数据"
    attractions_str = json.dumps(attractions, ensure_ascii=False, indent=2) if attractions else "暂无景点数据"

    # 组装提示词：SystemMessage 定义角色和输出格式，HumanMessage 包含用户具体需求和搜索结果
    prompt = [
        SystemMessage(content=ITINERARY_SYSTEM_PROMPT),
        HumanMessage(
            content=ITINERARY_USER_TEMPLATE.format(destination=destination, start_date=start_date, end_date=end_date,
                                                   budget=budget, num_travelers=num_travelers, interests=interests,
                                                   flights=flights_str, hotels=hotels_str, attractions=attractions_str,
                                                   num_days=num_days))
    ]

    # 获取 LLM 实例并调用生成行程
    llm = get_llm(fast=True)
    try:
        data = await invoke_structured_json(llm=llm,
                                           schema=ItineraryResult,
                                           messages=prompt)
        # model_dump(mode="json") 将 Pydantic 模型转为 JSON-safe dict，
        # 与 TravelPlanningState 的 list[dict] 类型兼容。
        itinerary = [day.model_dump(mode="json") for day in data.itinerary]
        return {
            "messages": [AIMessage(content="行程生成完成")],
            "itinerary": itinerary,
            "next_step": "finalize_plan",
        }
    except StructuredOutputError:
        # JSON 解析失败——LLM 返回格式不符合预期。
        # 返回通用错误消息并以 next_step="" 终止 graph，
        # 避免将无效数据传播到下游节点。
        return {
            "messages": [
                AIMessage(content="处理您的请求时遇到问题，请稍后重试。")
            ],
            "next_step": "",  # 终止 graph，不进入搜索阶段
        }
