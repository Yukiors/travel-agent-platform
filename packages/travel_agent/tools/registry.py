from typing import Optional

from travel_agent.tools.base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if self.is_registered(tool.name):
            return
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """列出所有已注册工具的名称。"""
        return list(self._tools.keys())

    def list(self) -> list[BaseTool]:
        """列出所有已注册工具实例。"""
        return list(self._tools.values())

    def is_registered(self, name: str) -> bool:
        return name in self._tools


_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = _build_tool_registry()
    return _registry


def reset_tool_registry() -> None:
    global _registry
    _registry = None  # 下次 get 时自动重建


def _build_tool_registry() -> ToolRegistry:
    """创建工具注册表。"""
    from travel_agent.tools.attraction import AttractionTool
    from travel_agent.tools.exchange_rate import ExchangeRateTool
    from travel_agent.tools.flight import FlightTool
    from travel_agent.tools.hotel import HotelTool
    from travel_agent.tools.weather import WeatherTool

    registry = ToolRegistry()
    registry.register(FlightTool())
    registry.register(HotelTool())
    registry.register(AttractionTool())
    registry.register(WeatherTool())
    registry.register(ExchangeRateTool())
    return registry
