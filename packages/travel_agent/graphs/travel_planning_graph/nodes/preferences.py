"""Node for gathering and validating user travel preferences.

本模块是 Travel Planning LangGraph 的第一个节点，
负责从用户的自然语言消息中提取结构化的旅行偏好，
并根据信息完整性决定继续搜索还是返回追问。

数据流:
    用户消息 → LLM 提取偏好 → JSON 解析
        ├─ is_complete=true  → 写入 state 字段, next_step="search_flights"
        └─ is_complete=false → 返回澄清问题, next_step="" (graph END)
"""

import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.llm import get_llm
from travel_agent.prompts import PREFERENCES_SYSTEM_PROMPT, PREFERENCES_USER_TEMPLATE


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
    # =========================================================================
    # 第 1 步：从对话历史中取出最后一条用户消息
    # =========================================================================
    # state.messages 是一个 LangChain BaseMessage 序列，其中可能
    # 夹杂 AIMessage（系统回复），需要过滤出 HumanMessage（用户消息）。
    user_messages = [
        m for m in state.messages if isinstance(m, HumanMessage)
    ]

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

    # 异步调用 LLM，不阻塞事件循环
    response = await llm.ainvoke(prompt)

    # =========================================================================
    # 第 3 步：清洗 LLM 原始输出，解析为 JSON
    # =========================================================================
    # response.content 是 LLM 返回的原始字符串，可能被 markdown 代码块包裹。
    # _clean_json_response 负责剥掉 ```json ... ``` 等包裹，返回纯 JSON。
    response_content = _clean_json_response(str(response.content))

    try:
        data = json.loads(response_content)
    except json.JSONDecodeError:
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
    is_complete = data.get("is_complete", False)

    if is_complete:
        # ----- 分支 A：信息完整，写入 state 并路由到搜索阶段 -----
        return {
            # 用户可见的确认消息
            "messages": [
                AIMessage(content="已了解您的需求，正在为您搜索...")
            ],
            # 将 LLM 提取的偏好写入 state 对应字段
            "destination": data.get("destination", ""),
            "start_date": data.get("start_date", ""),
            "end_date": data.get("end_date", ""),
            "budget": data.get("budget"),  # None 表示用户未指定预算
            "num_travelers": data.get("num_travelers", 1),  # 默认 1 人
            "interests": data.get("interests", []),  # 默认无特殊偏好
            # 路由到第一个搜索节点
            "next_step": "search_flights",
        }
    else:
        # ----- 分支 B：信息不完整，返回 LLM 生成的追问 -----
        # clarifying_question 由 LLM 在 prompt 中根据缺失字段生成，
        # 语气自然友好，例如 "请问您计划什么时候出发呢？"
        clarifying_question = data.get(
            "clarifying_question",
            "请补充更多旅行信息。"  # fallback：LLM 漏字段时的默认追问
        )
        return {
            "messages": [AIMessage(content=clarifying_question)],
            "next_step": "",  # 空字符串 → router 返回 END → graph 停止
            # 用户看到追问后可再次发送消息补全信息
        }
