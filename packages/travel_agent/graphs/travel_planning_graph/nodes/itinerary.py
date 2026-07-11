"""Node for building the final travel itinerary."""

import json
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.prompts import ITINERARY_SYSTEM_PROMPT, ITINERARY_USER_TEMPLATE


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
            raw = raw[first_newline + 1:]  # 去掉 ```json 这一整行

        # 去掉末尾的 ```（可能在最后一行或紧贴内容）
        if raw.endswith("```"):
            raw = raw[:-3]

    # 再次 strip，去除 fence 行剥离后可能残留的空白
    return raw.strip()


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
        HumanMessage(content=ITINERARY_USER_TEMPLATE.format(destination=destination, start_date=start_date, end_date=end_date, budget=budget, num_travelers=num_travelers, interests=interests, flights=flights_str, hotels=hotels_str, attractions=attractions_str, num_days=num_days))
    ]

    # 获取 LLM 实例并调用生成行程
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
        itinerary = json.loads(json_str)
        return {
            "messages": [AIMessage(content="行程生成完成")],
            "itinerary": itinerary,
            "next_step": "finalize_plan",
        }
    except json.JSONDecodeError:
        # JSON 解析失败，返回错误提示并终止后续流程
        return {
            "messages": [AIMessage(content="处理您的请求时遇到问题，请稍后重试。")],
            "next_step": "",
        }
