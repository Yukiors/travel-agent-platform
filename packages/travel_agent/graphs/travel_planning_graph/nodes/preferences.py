"""Node for gathering and validating user travel preferences.

本模块是 Travel Planning LangGraph 的第一个节点，
负责从用户的自然语言消息中提取结构化的旅行偏好，
并根据信息完整性决定继续搜索还是返回追问。

数据流:
    用户消息 → LLM 提取偏好 → JSON 解析
        ├─ is_complete=true  → 写入 state 字段, next_step="search_flights"
        └─ is_complete=false → 返回澄清问题, next_step="" (graph END)
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import ValidationError
from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.prompts import PREFERENCES_SYSTEM_PROMPT, PREFERENCES_USER_TEMPLATE
from travel_agent.llm.structured import invoke_structured_json, StructuredOutputError
from travel_agent.schemas import TravelPreferenceExtraction, ValidTravelRequest

REQUIRED_FIELDS: dict[str, str] = {
    "destination": "目的地",
    "start_date": "出发日期",
    "end_date": "返程日期",
}


def build_clarifying_question(missing_fields: list[str]) -> str:
    labels = [REQUIRED_FIELDS.get(f, f) for f in missing_fields]
    return f"请补充以下旅行信息：{'、'.join(labels)}。"


async def gather_preferences(state: TravelPlanningState) -> dict:
    """从对话中提取并校验用户的旅行偏好。

    这是 LangGraph workflow 的入口节点。它读取 state.messages 中
    最后一条用户消息，调用 LLM（fast 模型）提取结构化偏好，
    并根据必填字段完整性决定下一步路由。

    必填字段（三者缺一不可）:
        - destination: 目的地
        - start_date: 出发日期 (YYYY-MM-DD)
        - end_date:   返程日期 (YYYY-MM-DD)

    Args:
        state: LangGraph 共享状态，包含对话消息和所有中间结果。

    Returns:
        dict: 需要更新到 state 的字段。LangGraph 会自动将返回的 dict
              按字段名 merge 回 TravelPlanningState。

        返回值包含:
            - messages:   [AIMessage] 用户可见的回复
            - next_step:  str 路由键，"" 表示结束，"search_flights" 表示继续

        以及（当 is_complete=true 时额外写入）:
            - destination, start_date, end_date, budget,
              num_travelers, interests
    """
    import sys
    # =========================================================================
    # 第 1 步：从对话历史中取出最后一条用户消息
    # =========================================================================
    # state.messages 是一个 LangChain BaseMessage 序列，其中可能
    # 夹杂 AIMessage（系统回复），需要过滤出 HumanMessage（用户消息）。
    user_messages = [
        m for m in state.messages if isinstance(m, HumanMessage)
    ]
    print(f"GATHER_DEBUG: total_messages={len(state.messages)}, human_messages={len(user_messages)}", file=sys.stderr,
          flush=True)
    if user_messages:
        raw = str(user_messages[-1].content)
        print(
            f"GATHER_DEBUG: last_user_msg_len={len(raw)}, has_dest={'杭州' in raw}, has_cn={any('一' <= c <= '鿿' for c in raw)}",
            file=sys.stderr, flush=True)

    # 如果没有找到任何用户消息（异常情况，如空 state 直接调用），
    # 返回一条提示消息并终止 graph（next_step=""）。
    if not user_messages:
        return {
            "messages": [AIMessage(content="请提供您的旅行偏好信息。")],
            "next_step": "",  # 空字符串 → router 返回 END → graph 停止
        }

    # 取最后一条用户消息的文本内容
    user_message = user_messages[-1].content

    # =========================================================================
    # 第 2 步：构建 prompt 并调用 LLM 提取偏好
    # =========================================================================
    # 使用 fast 模型（当前默认 deepseek-chat），偏好提取是低成本任务。
    llm = get_llm(fast=True)

    # 组装 SystemMessage（角色 + 输出格式）和 HumanMessage（用户输入）
    prompt = [
        SystemMessage(content=PREFERENCES_SYSTEM_PROMPT),
        HumanMessage(content=PREFERENCES_USER_TEMPLATE.format(
            user_message=user_message
        )),
    ]

    try:
        extracted = invoke_structured_json(llm=llm,
                                           schema=TravelPreferenceExtraction,
                                           messages=prompt)
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

    # =========================================================================
    # 第 4 步：根据 is_complete 分流处理
    # =========================================================================
    # is_complete 由 LLM 在 prompt 中判定：
    #   - true:  destination、start_date、end_date 三者齐全且合法
    #   - false: 缺少任一必填字段
    #
    # 使用 .get() 安全取值并设默认值——防御 LLM 漏字段的情况。
    missing_fields = [
        field_name
        for field_name in REQUIRED_FIELDS
        if getattr(extracted, field_name) is None
    ]
    if missing_fields:
        # ----- 分支 B：信息不完整，提示用户补充信息 -----
        question = (
                extracted.clarifying_question
                or build_clarifying_question(missing_fields)
        )

        return {
            "messages": [AIMessage(content=question)],
            "next_step": "",
        }
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
        errors = "; ".join(
            error["msg"]
            for error in exc.errors()
        )

        return {
            "messages": [
                AIMessage(content=f"旅行信息存在问题：{errors}。请重新确认。")
            ],
            "next_step": "",
        }

        # mode="json" 会将 date 转换为 YYYY-MM-DD 字符串，
        # 与当前 TravelPlanningState 保持兼容。
    data = request.model_dump(mode="json")

    return {
        "messages": [
            AIMessage(content="已了解您的需求，正在为您搜索...")
        ],
        **data,
        "next_step": "search_all_parallel",
    }
