"""Travel planning API routes."""

import uuid
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from apps.api.schemas.travel import (
    TravelPlanRequest,
    TravelPlanResponse,
    TravelPlanStreamResponse,
)
from packages.travel_agent.graphs.travel_planning_graph.graph import build_travel_planning_graph

router = APIRouter()

# 全局图实例
_graph = None


def get_graph():
    """获取旅行规划图实例（单例模式）。"""
    global _graph
    if _graph is None:
        _graph = build_travel_planning_graph()
    return _graph


@router.post("/plan", response_model=TravelPlanResponse)
async def create_travel_plan(request: TravelPlanRequest) -> TravelPlanResponse:
    """生成旅行计划。"""
    graph = get_graph()

    # 构建用户消息
    user_message = f"我想去{request.preferences.destination}旅游，从{request.preferences.start_date}到{request.preferences.end_date}"
    if request.preferences.budget:
        user_message += f"，预算{request.preferences.budget}元/人"
    if request.preferences.num_travelers > 1:
        user_message += f"，{request.preferences.num_travelers}个人"
    if request.preferences.interests:
        user_message += f"，喜欢{','.join(request.preferences.interests)}"

    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content=user_message)]
    }

    # 生成配置
    plan_id = request.conversation_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": plan_id}}

    # 执行图
    result = await graph.ainvoke(initial_state, config)

    # 构建响应
    return TravelPlanResponse(
        plan_id=plan_id,
        destination=result.get("destination", ""),
        itinerary=result.get("itinerary", []),
        final_plan=result.get("final_plan", {}),
        total_budget_estimate=result.get("total_budget_estimate", 0.0),
        created_at=datetime.now(),
    )


@router.post("/plan/stream")
async def create_travel_plan_stream(request: TravelPlanRequest):
    """流式生成旅行计划。"""
    graph = get_graph()

    # 构建用户消息
    user_message = f"我想去{request.preferences.destination}旅游，从{request.preferences.start_date}到{request.preferences.end_date}"
    if request.preferences.budget:
        user_message += f"，预算{request.preferences.budget}元/人"
    if request.preferences.num_travelers > 1:
        user_message += f"，{request.preferences.num_travelers}个人"
    if request.preferences.interests:
        user_message += f"，喜欢{','.join(request.preferences.interests)}"

    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content=user_message)]
    }

    # 生成配置
    plan_id = request.conversation_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": plan_id}}

    async def event_generator() -> AsyncGenerator[str, None]:
        """生成服务端事件流。"""
        import json

        async for event in graph.astream(initial_state, config):
            # 发送当前节点状态
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        # 发送完成标记
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
