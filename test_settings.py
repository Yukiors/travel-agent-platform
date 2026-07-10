from packages.common.config import Settings, get_settings

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import json
from travel_agent.graphs.travel_planning_graph.state import TravelPlanningState
from travel_agent.prompts import FLIGHTS_SYSTEM_PROMPT, FLIGHTS_USER_TEMPLATE, HOTELS_SYSTEM_PROMPT, \
    HOTELS_USER_TEMPLATE, ITINERARY_SYSTEM_PROMPT, ITINERARY_USER_TEMPLATE
from travel_agent.llm import get_llm


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


if __name__ == '__main__':
    llm = get_llm(fast=True)

    # 组装 SystemMessage（角色 + 输出格式）和 HumanMessage（用户输入）
    prompt = [
        SystemMessage(content=FLIGHTS_SYSTEM_PROMPT),
        HumanMessage(content=FLIGHTS_USER_TEMPLATE.format(destination="杭州", start_date='2026-07-10', end_date='2026-07-15', budget=5000, num_travelers=1, interests='')),
    ]

    response = llm.invoke(prompt)
    response = _clean_json_response(str(response.content))

    print(response)
