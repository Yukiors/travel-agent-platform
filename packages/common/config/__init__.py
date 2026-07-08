"""应用配置模块。

通过 pydantic-settings 从环境变量和 .env 文件加载配置。
对外暴露 Settings 类和 get_settings() 工厂函数。

使用方式:
    from common.config import get_settings
    settings = get_settings()  # 全局单例，带自动校验
"""
from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
