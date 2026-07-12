"""Travel planning API routes."""

import json
import logging
import traceback
import uuid
from datetime import date, datetime
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


def _build_user_message(request: TravelPlanRequest) -> str:
    """从请求中的结构化偏好构建用户消息字符串。"""
    prefs = request.preferences
    parts = [f"我想去{prefs.destination}旅游"]

    if prefs.start_date and prefs.end_date:
        parts.append(f"从{prefs.start_date}到{prefs.end_date}")
    if prefs.budget:
        parts.append(f"预算{prefs.budget}元/人")
    if prefs.num_travelers and prefs.num_travelers > 1:
        parts.append(f"{prefs.num_travelers}个人")
    if prefs.interests:
        parts.append(f"喜欢{','.join(prefs.interests)}")

    return "，".join(parts)


def _is_preferences_complete(prefs) -> bool:
    """检查结构化偏好是否包含三个必填字段。"""
    return bool(prefs.destination and prefs.start_date and prefs.end_date)


def _build_initial_state(request: TravelPlanRequest) -> dict:
    """构建图执行的初始状态。

    当 API 收到完整的结构化偏好时（destination + start_date + end_date 齐全），
    直接将偏好写入初始 state，绕过 gather_preferences 节点的 LLM 提取，
    让图直接进入 search_all_parallel 阶段。

    偏好不完整时仅包含用户消息，让 gather_preferences 节点走 LLM 提取流程。
    """
    prefs = request.preferences

    if _is_preferences_complete(prefs):
        # 结构化直通：偏好完整 → 直接写入 state，跳过提取LLM
        try:
            sd = date.fromisoformat(prefs.start_date) if isinstance(prefs.start_date, str) else prefs.start_date
            ed = date.fromisoformat(prefs.end_date) if isinstance(prefs.end_date, str) else prefs.end_date
        except (ValueError, TypeError):
            # 日期格式无效 → 回退到 LLM 提取
            return {
                "messages": [HumanMessage(content=_build_user_message(request))]
            }

        return {
            "messages": [HumanMessage(content=_build_user_message(request))],
            "destination": prefs.destination,
            "start_date": str(sd),
            "end_date": str(ed),
            "budget": prefs.budget,
            "num_travelers": prefs.num_travelers or 1,
            "interests": prefs.interests or [],
            "next_step": "search_all_parallel",
        }

    # 偏好不完整 → 走 LLM 提取流程
    return {
        "messages": [HumanMessage(content=_build_user_message(request))]
    }


def _safe_get(result, key, default):
    """安全地从 result 中取值，兼容 dict 和 dataclass/object 两种返回类型。"""
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)


@router.post("/plan", response_model=TravelPlanResponse)
async def create_travel_plan(request: TravelPlanRequest) -> TravelPlanResponse:
    """生成旅行计划。

    当请求中 destination、start_date、end_date 齐全时，
    绕过偏好提取 LLM，直接进入搜索阶段以节省延迟和成本。
    """
    graph = get_graph()

    # 构建初始状态（支持结构化直通）
    initial_state = _build_initial_state(request)

    # 生成配置 — conversation_id 用于多轮会话状态持久化
    plan_id = request.conversation_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": plan_id}}

    # 执行图
    try:
        result = await graph.ainvoke(initial_state, config)
    except Exception as e:
        logger.error(f"旅行规划图执行失败: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=502,
            detail=f"旅行规划服务暂时不可用: {str(e)}",
        )

    # 构建响应
    try:
        msgs = _safe_get(result, "messages", [])
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "messages count=%d, next_step=%r",
                len(msgs), _safe_get(result, "next_step", ""),
            )
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

    initial_state = _build_initial_state(request)

    plan_id = request.conversation_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": plan_id}}

    async def event_generator() -> AsyncGenerator[str, None]:
        """生成服务端事件流。"""
        try:
            async for event in graph.astream(initial_state, config):
                yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
        except Exception as e:
            logger.error(f"流式规划执行失败: {e}\n{traceback.format_exc()}")
            error_data = json.dumps(
                {"error": f"旅行规划服务暂时不可用: {str(e)}"},
                ensure_ascii=False,
            )
            yield f"data: {error_data}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
