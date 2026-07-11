"""旅行工具层 —— 可替换的工具抽象。

提供:
- BaseTool: 所有工具的抽象基类
- BaseMockTool: Mock 工具基类（确定性种子）
- ToolRegistry: 工具注册中心（按名称查找/替换）
- get_tool_registry(): 全局单例注册中心

使用示例:
    from travel_agent.tools import get_tool_registry

    registry = get_tool_registry()
    tool = registry.get("hotels")
    result = await tool.execute(destination="北京", ...)
"""

from travel_agent.tools.base import BaseMockTool, BaseTool
from travel_agent.tools.registry import (
    ToolRegistry,
    get_tool_registry,
    reset_tool_registry,
)

__all__ = [
    "BaseTool",
    "BaseMockTool",
    "ToolRegistry",
    "get_tool_registry",
    "reset_tool_registry",
]
