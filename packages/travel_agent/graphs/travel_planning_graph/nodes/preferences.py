"""Node for gathering and validating user travel preferences.

本模块是 Travel Planning LangGraph 的第一个节点，
负责从用户的自然语言消息中提取结构化的旅行偏好，
并根据信息完整性决定继续搜索还是返回追问。

数据流:
    用户消息 → LLM 提取偏好 → JSON 解析
        ├─ is_complete=true  → 写入 state 字段, next_step="search_flights"
        └─ is_complete=false → 返回澄清问题, next_step="" (graph END)
"""

import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import ValidationError

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.llm.structured import StructuredOutputError, invoke_structured_json
from travel_agent.prompts import PREFERENCES_SYSTEM_PROMPT, PREFERENCES_USER_TEMPLATE
from travel_agent.schemas import TravelPreferenceExtraction, ValidTravelRequest

REQUIRED_FIELDS: dict[str, str] = {
    "destination": "目的地",
    "start_date": "出发日期",
    "end_date": "返程日期",
}


def build_clarifying_question(missing_fields: list[str]) -> str:
    labels = [REQUIRED_FIELDS.get(f, f) for f in missing_fields]
    return f"请补充以下旅行信息：{'、'.join(labels)}。"


def _merge_existing_preferences(state: TravelPlanningState) -> dict[str, object]:
    """从 state 中提取已有的有效偏好（多轮会话合并）。

    当用户在追问后补充信息时，state 中可能已经有一轮提取的偏好
    （如 destination 已在前一轮确认），应保留这些值作为 LLM 的
    补充上下文，避免 LLM 漏掉已确认的信息。
    """
    existing: dict[str, object] = {}
    if state.destination:
        existing["destination"] = state.destination
    if state.start_date:
        existing["start_date"] = state.start_date
    if state.end_date:
        existing["end_date"] = state.end_date
    if state.budget is not None:
        existing["budget"] = state.budget
    if state.num_travelers and state.num_travelers != 1:
        existing["num_travelers"] = state.num_travelers
    if state.interests:
        existing["interests"] = state.interests
    return existing


def _preferences_already_complete(state: TravelPlanningState) -> bool:
    """检查 state 中是否已有完整的必填偏好（结构化 API 直通场景）。"""
    return bool(
        state.destination
        and state.start_date
        and state.end_date
    )


async def gather_preferences(state: TravelPlanningState) -> dict:
    """从对话中提取并校验用户的旅行偏好。

    这是 LangGraph workflow 的入口节点。它读取 state.messages 中
    最后一条用户消息，调用 LLM（fast 模型）提取结构化偏好，
    并根据必填字段完整性决定下一步路由。

    支持两种场景：
    1. 结构化直通：state 中已有完整的 destination + start_date + end_date
       （来自 API 层直接注入），跳过 LLM 提取直接进入搜索。
    2. LLM 提取：从用户消息中提取偏好（支持多轮会话合并）。
    """
    # =========================================================================
    # 第 1 步：检查是否结构化直通
    # =========================================================================
    if _preferences_already_complete(state):
        print("GATHER_DEBUG: structured bypass — preferences already complete", file=sys.stderr, flush=True)
        return {
            "messages": [AIMessage(content="已了解您的需求，正在为您搜索...")],
            "next_step": "search_all_parallel",
        }

    # =========================================================================
    # 第 2 步：从对话历史中取出最后一条用户消息
    # =========================================================================
    user_messages = [
        m for m in state.messages if isinstance(m, HumanMessage)
    ]
    print(
        f"GATHER_DEBUG: total_messages={len(state.messages)}, human_messages={len(user_messages)}",
        file=sys.stderr, flush=True,
    )

    if not user_messages:
        return {
            "messages": [AIMessage(content="请提供您的旅行偏好信息。")],
            "next_step": "",
        }

    user_message = user_messages[-1].content

    # =========================================================================
    # 第 3 步：多轮会话 — 合并已有偏好作为上下文
    # =========================================================================
    existing = _merge_existing_preferences(state)
    context_note = ""
    if existing:
        context_note = (
            "\n\n【已确认的偏好（来自之前的对话，请保留以下信息并在此基础上"
            "从用户消息中提取新增信息）】\n" +
            "\n".join(f"- {k}: {v}" for k, v in existing.items())
        )

    # =========================================================================
    # 第 4 步：构建 prompt 并调用 LLM 提取偏好
    # =========================================================================
    llm = get_llm(fast=True)

    prompt = [
        SystemMessage(content=PREFERENCES_SYSTEM_PROMPT),
        HumanMessage(content=(
            PREFERENCES_USER_TEMPLATE.format(user_message=user_message) +
            context_note
        )),
    ]

    try:
        extracted = await invoke_structured_json(
            llm=llm,
            schema=TravelPreferenceExtraction,
            messages=prompt,
        )
    except StructuredOutputError:
        return {
            "messages": [
                AIMessage(content="处理您的请求时遇到问题，请稍后重试。")
            ],
            "next_step": "",
        }

    # =========================================================================
    # 第 5 步：多轮合并 — 用已有偏好回填 LLM 未返回的字段
    # =========================================================================
    for field_name, value in existing.items():
        if getattr(extracted, field_name) is None:
            setattr(extracted, field_name, value)

    # =========================================================================
    # 第 6 步：必填字段完整性检查
    # =========================================================================
    missing_fields = [
        field_name
        for field_name in REQUIRED_FIELDS
        if getattr(extracted, field_name) is None
    ]
    if missing_fields:
        question = (
            extracted.clarifying_question
            or build_clarifying_question(missing_fields)
        )
        return {
            "messages": [AIMessage(content=question)],
            "next_step": "",
        }

    # =========================================================================
    # 第 7 步：校验并写入 state
    # =========================================================================
    try:
        request = ValidTravelRequest(
            destination=extracted.destination,
            start_date=extracted.start_date,
            end_date=extracted.end_date,
            budget=extracted.budget,
            num_travelers=extracted.num_travelers,
            interests=extracted.interests,
        )
    except ValidationError as exc:
        errors = "; ".join(error["msg"] for error in exc.errors())
        return {
            "messages": [
                AIMessage(content=f"旅行信息存在问题：{errors}。请重新确认。")
            ],
            "next_step": "",
        }

    data = request.model_dump(mode="json")

    return {
        "messages": [
            AIMessage(content="已了解您的需求，正在为您搜索...")
        ],
        **data,
        "next_step": "search_all_parallel",
    }
