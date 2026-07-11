# packages/travel_agent/llm/structured.py

from typing import Type, TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(RuntimeError):
    """LLM 没有返回可验证的结构化数据。"""


def _clean_json_response(raw: str) -> str:
    """清洗 LLM 返回的原始字符串，去除 markdown 代码块包裹和首尾空白。

    LLM 经常不按指令直接输出裸 JSON，而是用 markdown 代码块包裹，
    如 ```json ... ``` 或 ``` ... ```。本函数负责将这些包裹剥掉，
    返回纯 JSON 字符串供 model_validate_json 解析。
    """
    raw = raw.strip()

    if raw.startswith("```"):
        first_newline = raw.find("\n")
        if first_newline != -1:
            raw = raw[first_newline + 1:]

        if raw.endswith("```"):
            raw = raw[:-3]

    return raw.strip()


async def invoke_structured_json(
        llm: BaseChatModel,
        schema: Type[T],
        messages: list[BaseMessage]
) -> T:
    """调用 LLM，返回结构化 JSON（Pydantic 模型实例）。

    Args:
        llm: 已配置的 LangChain 聊天模型实例。
        schema: Pydantic 模型**类**（非实例），用于验证 LLM 输出。
        messages: 发送给 LLM 的消息列表。

    Returns:
        通过 schema 验证后的 Pydantic 模型实例。

    Raises:
        StructuredOutputError: LLM 返回空内容或 JSON 不符合 schema。
    """
    json_llm = llm.bind(response_format={"type": "json_object"})

    response = await json_llm.ainvoke(messages)

    content = response.content

    if not isinstance(content, str) or not content.strip():
        raise StructuredOutputError("LLM 返回了空内容")

    # 先清洗 markdown 代码块，再用 Pydantic 验证
    cleaned = _clean_json_response(content)

    try:
        return schema.model_validate_json(cleaned)
    except ValidationError as exc:
        raise StructuredOutputError(
            f"LLM 输出不符合 {schema.__name__}：{exc}"
        ) from exc
