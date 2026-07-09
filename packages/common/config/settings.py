"""
应用全局配置模块。

使用 pydantic-settings 实现类型安全的配置管理，
按优先级从高到低加载：环境变量 > .env 文件 > 代码默认值。
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# 计算项目根目录——与 CWD 解耦
# 本文件位于: packages/common/config/settings.py
# 项目根目录: 往上 3 级 (config → common → packages → 项目根)
# ---------------------------------------------------------------------------
_project_root = Path(__file__).resolve().parent.parent.parent.parent
_ENV_FILE = str(_project_root / ".env")


class Settings(BaseSettings):
    """应用全局配置类。

    所有配置项通过环境变量或 .env 文件注入，
    类属性名即为配置项名（小写），可通过大写别名从环境变量读取。

    使用方式:
        from common.config import get_settings
        settings = get_settings()
        print(settings.deepseek_api_key)
    """

    # ---- pydantic-settings 模型配置 ----
    model_config = SettingsConfigDict(
        # 使用绝对路径，无论从哪个目录启动都能正确加载 .env
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        # 忽略 .env 中不在模型中定义的多余字段，避免启动报错
        extra="ignore",
    )

    # =========================================================================
    # DeepSeek API 配置
    # =========================================================================

    # DeepSeek API 密钥，必填，环境变量名 DEEPSEEK_API_KEY
    # 默认值为空字符串，启动时 validate_api_keys() 会检查是否已配置
    deepseek_api_key: str = Field(
        default="",
        validation_alias="DEEPSEEK_API_KEY",
    )

    # DeepSeek 主力模型，用于行程生成等高质量任务
    # deepseek-chat 对应 DeepSeek-V3，性价比最高的旗舰模型
    deepseek_model: str = Field(
        default="deepseek-chat",
        validation_alias="DEEPSEEK_MODEL",
    )

    # DeepSeek 轻量模型别名（当前 DeepSeek 平台主要提供 deepseek-chat，
    # 所有节点统一使用同一模型，预留此字段方便后续切换）
    deepseek_model_fast: str = Field(
        default="deepseek-chat",
        validation_alias="DEEPSEEK_MODEL_FAST",
    )

    # =========================================================================
    # 调试开关
    # =========================================================================

    # 开启后输出详细日志、异常堆栈；生产环境应设为 false
    debug: bool = Field(
        default=False,
        validation_alias="DEBUG",
    )

    # =========================================================================
    # 计算属性
    # =========================================================================

    @property
    def deepseek_base_url(self) -> str:
        """DeepSeek API 的 OpenAI 兼容端点地址。

        DeepSeek 提供与 OpenAI SDK 完全兼容的 HTTP API，
        因此可以直接使用 langchain-openai 的 ChatOpenAI 类调用。
        """
        return "https://api.deepseek.com/v1"

    # =========================================================================
    # 配置校验
    # =========================================================================

    def validate_api_keys(self) -> None:
        """校验必填的 API 密钥是否已正确配置。

        在应用启动时调用（通过 get_settings()），
        避免运行到一半才发现密钥缺失。

        Raises:
            ValueError: 如果必填密钥为空或仍为占位符值。
        """
        missing: list[str] = []

        # 遍历所有需要校验的密钥 —— 当前只有 DeepSeek
        for key_name, key_value in [
            ("DEEPSEEK_API_KEY", self.deepseek_api_key),
        ]:
            # 检查：值为空，或者仍是占位符（以 "your_" 开头）
            if not key_value or key_value.startswith("your_"):
                missing.append(key_name)

        if missing:
            raise ValueError(
                f"以下 API 密钥未配置或仍为占位符: {', '.join(missing)}。"
                f"请在 .env 文件中设置（参考 .env.example 模板）。"
            )


# =============================================================================
# 工厂函数
# =============================================================================


# @lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取 Settings 单例（带缓存）。

    使用 lru_cache 确保全局只有一个 Settings 实例，
    避免每次调用都重新读取 .env 文件。

    首次调用时自动执行配置校验（validate_api_keys），
    校验失败则抛出异常，阻止应用启动。

    Returns:
        Settings: 已校验的全局配置实例。

    Raises:
        ValidationError: pydantic 字段校验失败（如类型不匹配）。
        ValueError: 必填 API 密钥缺失或未配置。
    """
    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValidationError as e:
        # 包装校验错误，提供更友好的错误消息
        raise ValidationError.from_exception_data(
            title="应用配置错误",
            line_errors=e.errors(),
        ) from e

    # 启动时即校验密钥，fast-fail 优于运行时才发现
    # settings.validate_api_keys()

    return settings
