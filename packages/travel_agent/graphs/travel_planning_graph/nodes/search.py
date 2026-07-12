"""Nodes for searching flights, hotels, and attractions."""

import asyncio
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.llm.structured import StructuredOutputError, invoke_structured_json
from travel_agent.prompts import (
    ATTRACTIONS_SYSTEM_PROMPT,
    ATTRACTIONS_USER_TEMPLATE,
    FLIGHTS_SYSTEM_PROMPT,
    FLIGHTS_USER_TEMPLATE,
    HOTELS_SYSTEM_PROMPT,
    HOTELS_USER_TEMPLATE,
)
from travel_agent.schemas import AttractionSearchResult, FlightSearchResult, HotelSearchResult


def _dump(items: list) -> list[dict]:
    """将 Pydantic 模型列表转为 JSON-safe dict 列表，写入 State。"""
    return [item.model_dump(mode="json") for item in items]


async def _search_flights_internal(state: TravelPlanningState) -> dict:
    """内部异步方法：执行航班搜索逻辑。"""
    destination = state.destination
    start_date = state.start_date
    end_date = state.end_date
    budget = state.budget or 0.0
    num_travelers = state.num_travelers
    interests = state.interests

    llm = get_llm(fast=True)

    messages = [
        SystemMessage(content=FLIGHTS_SYSTEM_PROMPT),
        HumanMessage(
            content=FLIGHTS_USER_TEMPLATE.format(
                destination=destination, start_date=start_date, end_date=end_date,
                budget=budget, num_travelers=num_travelers, interests=interests,
            )),
    ]

    try:
        data = await invoke_structured_json(
            llm=llm, schema=FlightSearchResult, messages=messages,
        )
        return {"flights": _dump(data.flights)}
    except StructuredOutputError:
        return {"flights": None, "error": True}


async def _search_hotels_internal(state: TravelPlanningState) -> dict:
    """内部异步方法：执行酒店搜索逻辑。"""
    destination = state.destination
    start_date = state.start_date
    end_date = state.end_date
    budget = state.budget or 0.0
    num_travelers = state.num_travelers
    interests = state.interests

    llm = get_llm(fast=True)

    messages = [
        SystemMessage(content=HOTELS_SYSTEM_PROMPT),
        HumanMessage(
            content=HOTELS_USER_TEMPLATE.format(
                destination=destination, start_date=start_date, end_date=end_date,
                budget=budget, num_travelers=num_travelers, interests=interests,
            )),
    ]

    try:
        data = await invoke_structured_json(
            llm=llm, schema=HotelSearchResult, messages=messages,
        )
        return {"hotels": _dump(data.hotels)}
    except StructuredOutputError:
        return {"hotels": None, "error": True}


async def _search_attractions_internal(state: TravelPlanningState) -> dict:
    """内部异步方法：执行景点和餐厅搜索逻辑。"""
    destination = state.destination
    start_date = state.start_date
    end_date = state.end_date
    budget = state.budget or 0.0
    num_travelers = state.num_travelers
    interests = state.interests

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        return {"attractions": None, "error": True}
    num_days = (end - start).days + 1
    total_recommendations = num_days * 3

    llm = get_llm(fast=True)

    messages = [
        SystemMessage(content=ATTRACTIONS_SYSTEM_PROMPT),
        HumanMessage(
            content=ATTRACTIONS_USER_TEMPLATE.format(
                destination=destination, start_date=start_date, end_date=end_date,
                num_days=num_days, budget=budget, num_travelers=num_travelers,
                interests=interests, total_recommendations=total_recommendations,
            )),
    ]

    try:
        data = await invoke_structured_json(
            llm=llm, schema=AttractionSearchResult, messages=messages,
        )
        return {"attractions": _dump(data.attractions)}
    except StructuredOutputError:
        return {"attractions": None, "error": True}


async def search_flights(state: TravelPlanningState) -> dict:
    """根据用户的旅行需求搜索可用航班。"""
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
    """根据用户的旅行需求搜索可用酒店。"""
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
    """根据用户的旅行需求搜索景点和餐厅推荐。"""
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
    """并行搜索航班、酒店和景点，显著提升响应速度。"""
    results = await asyncio.gather(
        _search_flights_internal(state),
        _search_hotels_internal(state),
        _search_attractions_internal(state),
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
