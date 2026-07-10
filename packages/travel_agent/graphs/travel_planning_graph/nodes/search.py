"""Nodes for searching flights, hotels, and attractions."""

import asyncio
import json
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.prompts import FLIGHTS_SYSTEM_PROMPT, FLIGHTS_USER_TEMPLATE, HOTELS_SYSTEM_PROMPT, \
    HOTELS_USER_TEMPLATE, ATTRACTIONS_SYSTEM_PROMPT, ATTRACTIONS_USER_TEMPLATE


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
    raw = raw.strip()

    if raw.startswith("```"):
        first_newline = raw.find("\n")
        if first_newline != -1:
            raw = raw[first_newline + 1:]

        if raw.endswith("```"):
            raw = raw[:-3]

    return raw.strip()


async def _search_flights_internal(state: TravelPlanningState) -> dict:
    """内部异步方法：执行航班搜索逻辑。

    Args:
        state: 旅行规划状态对象

    Returns:
        包含 flights 数据的字典，或错误标志
    """
    destination = state.destination
    start_date = state.start_date
    end_date = state.end_date
    budget = state.budget or 0.0
    num_travelers = state.num_travelers
    interests = state.interests

    llm = get_llm(fast=True)

    prompt = [
        SystemMessage(content=FLIGHTS_SYSTEM_PROMPT),
        HumanMessage(
            content=FLIGHTS_USER_TEMPLATE.format(destination=destination, start_date=start_date, end_date=end_date,
                                                 budget=budget, num_travelers=num_travelers, interests=interests)),
    ]

    response = await llm.ainvoke(prompt)
    response = _clean_json_response(str(response.content))

    try:
        data = json.loads(response)
        return {"flights": data}
    except json.JSONDecodeError:
        return {"flights": None, "error": True}


async def _search_hotels_internal(state: TravelPlanningState) -> dict:
    """内部异步方法：执行酒店搜索逻辑。

    Args:
        state: 旅行规划状态对象

    Returns:
        包含 hotels 数据的字典，或错误标志
    """
    destination = state.destination
    start_date = state.start_date
    end_date = state.end_date
    budget = state.budget or 0.0
    num_travelers = state.num_travelers
    interests = state.interests

    llm = get_llm(fast=True)

    prompt = [
        SystemMessage(content=HOTELS_SYSTEM_PROMPT),
        HumanMessage(
            content=HOTELS_USER_TEMPLATE.format(destination=destination, start_date=start_date, end_date=end_date,
                                                budget=budget, num_travelers=num_travelers, interests=interests)),
    ]

    response = await llm.ainvoke(prompt)
    response = _clean_json_response(str(response.content))

    try:
        data = json.loads(response)
        return {"hotels": data}
    except json.JSONDecodeError:
        return {"hotels": None, "error": True}


async def _search_attractions_internal(state: TravelPlanningState) -> dict:
    """内部异步方法：执行景点和餐厅搜索逻辑。

    Args:
        state: 旅行规划状态对象

    Returns:
        包含 attractions 数据的字典，或错误标志
    """
    destination = state.destination
    start_date = state.start_date
    end_date = state.end_date
    budget = state.budget or 0.0
    num_travelers = state.num_travelers
    interests = state.interests

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    num_days = (end - start).days + 1
    total_recommendations = num_days * 3

    llm = get_llm(fast=True)

    prompt = [
        SystemMessage(content=ATTRACTIONS_SYSTEM_PROMPT),
        HumanMessage(
            content=ATTRACTIONS_USER_TEMPLATE.format(destination=destination, start_date=start_date, end_date=end_date,
                                                     num_days=num_days, budget=budget, num_travelers=num_travelers,
                                                     interests=interests, total_recommendations=total_recommendations)),
    ]

    response = await llm.ainvoke(prompt)
    response = _clean_json_response(str(response.content))

    try:
        data = json.loads(response)
        return {"attractions": data}
    except json.JSONDecodeError:
        return {"attractions": None, "error": True}


async def search_flights(state: TravelPlanningState) -> dict:
    """根据用户的旅行需求搜索可用航班。

    使用 LLM 生成 2-3 个合理的航班选项，考虑目的地、日期、预算、人数等因素。
    返回的航班数据包含航班号、航空公司、时间、价格、中转次数等信息。

    Args:
        state: 旅行规划状态对象，包含目的地、日期、预算、人数、兴趣偏好等信息

    Returns:
        包含以下字段的字典：
        - messages: AIMessage 列表，包含搜索完成的提示信息
        - flights: 航班选项数据（JSON 数组格式）
        - next_step: 下一个要执行的节点名称（"search_hotels" 或空字符串表示终止）
    """
    result = await _search_flights_internal(state)

    if result.get("error"):
        return {
            "messages": [AIMessage(content="处理您的请求时遇到问题，请稍后重试。")],
            "next_step": "",
        }

    return {
        "messages": [AIMessage(content="航班搜索完成")],
        "flights": result["flights"],
        "next_step": "search_hotels",
    }


async def search_hotels(state: TravelPlanningState) -> dict:
    """根据用户的旅行需求搜索可用酒店。

    使用 LLM 生成 2-3 个合理的酒店选项，考虑目的地、日期、预算、人数等因素。
    返回的酒店数据包含名称、星级、地址、价格、入住/退房时间、亮点描述等信息。

    Args:
        state: 旅行规划状态对象，包含目的地、日期、预算、人数、兴趣偏好等信息

    Returns:
        包含以下字段的字典：
        - messages: AIMessage 列表，包含搜索完成的提示信息
        - hotels: 酒店选项数据（JSON 数组格式）
        - next_step: 下一个要执行的节点名称（"search_attractions" 或空字符串表示终止）
    """
    result = await _search_hotels_internal(state)

    if result.get("error"):
        return {
            "messages": [AIMessage(content="处理您的请求时遇到问题，请稍后重试。")],
            "next_step": "",
        }

    return {
        "messages": [AIMessage(content="酒店搜索完成")],
        "hotels": result["hotels"],
        "next_step": "search_attractions",
    }


async def search_attractions(state: TravelPlanningState) -> dict:
    """根据用户的旅行需求搜索景点和餐厅推荐。

    使用 LLM 生成适合的景点和餐厅推荐，考虑目的地、日期、预算、人数、兴趣偏好等因素。
    返回的数据包含名称、类型（景点/餐厅）、描述、推荐游玩时长、门票价格/人均消费等信息。

    Args:
        state: 旅行规划状态对象，包含目的地、日期、预算、人数、兴趣偏好等信息

    Returns:
        包含以下字段的字典：
        - messages: AIMessage 列表，包含搜索完成的提示信息
        - attractions: 景点和餐厅推荐数据（JSON 数组格式）
        - next_step: 下一个要执行的节点名称（"build_itinerary" 或空字符串表示终止）
    """
    result = await _search_attractions_internal(state)

    if result.get("error"):
        return {
            "messages": [AIMessage(content="处理您的请求时遇到问题，请稍后重试。")],
            "next_step": "",
        }

    return {
        "messages": [AIMessage(content="景点和餐厅搜索完成")],
        "attractions": result["attractions"],
        "next_step": "build_itinerary",
    }


async def search_all_parallel(state: TravelPlanningState) -> dict:
    """并行搜索航班、酒店和景点，显著提升响应速度。

    将三个独立的搜索任务（航班、酒店、景点）并行执行，而非串行等待。
    这将总响应时间从 3× 单次调用降低到 max(三者) 的时间。

    Args:
        state: 旅行规划状态对象，包含目的地、日期、预算、人数、兴趣偏好等信息

    Returns:
        包含以下字段的字典：
        - messages: AIMessage 列表，包含搜索完成的提示信息
        - flights: 航班选项数据（JSON 数组格式）
        - hotels: 酒店选项数据（JSON 数组格式）
        - attractions: 景点和餐厅推荐数据（JSON 数组格式）
        - next_step: 下一个要执行的节点名称（"build_itinerary" 或空字符串表示终止）

    处理流程：
        1. 使用 asyncio.gather 并行调用三个内部搜索方法
        2. 检查是否有任何搜索失败（error 标志）
        3. 如果全部成功，返回合并结果并继续流程
        4. 如果任意失败，返回错误信息并终止流程
    """
    results = await asyncio.gather(
        _search_flights_internal(state),
        _search_hotels_internal(state),
        _search_attractions_internal(state)
    )

    flights_result, hotels_result, attractions_result = results

    if any(r.get("error") for r in results):
        return {
            "messages": [AIMessage(content="处理您的请求时遇到问题，请稍后重试。")],
            "next_step": "",
        }

    return {
        "messages": [AIMessage(content="所有搜索完成")],
        "flights": flights_result["flights"],
        "hotels": hotels_result["hotels"],
        "attractions": attractions_result["attractions"],
        "next_step": "build_itinerary",
    }
