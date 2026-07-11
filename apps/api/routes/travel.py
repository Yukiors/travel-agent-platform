"""Travel planning API routes."""

import logging
import traceback
import uuid
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from apps.api.schemas.travel import (
    TravelPlanRequest,
    TravelPlanResponse,
    TravelPlanStreamResponse,
)
from travel_agent.graphs.travel_planning_graph.graph import build_travel_planning_graph

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局图实例
_graph = None


def get_graph():
    """获取旅行规划图实例（单例模式）。"""
    global _graph
    if _graph is None:
        _graph = build_travel_planning_graph()
    return _graph


def _safe_get(result, key, default):
    """安全地从 result 中取值，兼容 dict 和 dataclass/object 两种返回类型。

    LangGraph 的 ainvoke 在不同版本中可能返回 dict 或 typed state 实例。
    本函数同时支持 .get()（dict）和 getattr()（object）两种访问方式。
    """
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


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

    # 执行图——捕获所有异常以避免 500
    try:
        result = await graph.ainvoke(initial_state, config)
    except Exception as e:
        logger.error(f"旅行规划图执行失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=502,
            detail=f"旅行规划服务暂时不可用: {str(e)}",
        )

    # 构建响应——使用 _safe_get 兼容 dict 和 dataclass 两种返回类型
    try:
        import sys
        msgs = _safe_get(result, "messages", [])
        print(f"DEBUG messages count={len(msgs)}, next_step={_safe_get(result,'next_step','')!r}", file=sys.stderr, flush=True)
        for i, m in enumerate(msgs):
            print(f"DEBUG msg[{i}]: {str(m.content)[:200]}", file=sys.stderr, flush=True)
        return TravelPlanResponse(
            plan_id=plan_id,
            destination=_safe_get(result, "destination", ""),
            itinerary=_safe_get(result, "itinerary", []),
            final_plan=_safe_get(result, "final_plan", {}),
            total_budget_estimate=_safe_get(result, "total_budget_estimate", 0.0),
            created_at=datetime.now(),
        )
    except Exception as e:
        logger.error(f"构建旅行计划响应失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=502,
            detail=f"旅行计划结果解析失败: {str(e)}",
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

        try:
            async for event in graph.astream(initial_state, config):
                # 发送当前节点状态
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"流式规划执行失败: {e}\n{traceback.format_exc()}")
            error_data = json.dumps(
                {"error": f"旅行规划服务暂时不可用: {str(e)}"},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"

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
