"""
LLM 工厂模块。

封装 DeepSeek 模型的初始化逻辑，提供统一的模型获取入口。
DeepSeek 的 HTTP API 完全兼容 OpenAI 格式，
因此直接复用 langchain-openai 的 ChatOpenAI 类，
只需替换 base_url 即可接入，无需额外 SDK。
"""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from common.config.settings import get_settings


class LLMFactory:
    """LLM 工厂类，负责按需创建 DeepSeek 模型实例。

    从全局配置 get_settings() 中读取 API Key、模型名等参数，
    按任务复杂度提供两类模型：
    - 主力模型 (fast=False): 行程生成等高质量输出任务
    - 轻量模型 (fast=True):  偏好提取、模拟搜索等低成本任务

    设计为无状态（配置来自外部单例），每次调用 get_chat_model
    都会创建新的 ChatOpenAI 实例 —— LangChain 的 ChatOpenAI
    本身是轻量对象（仅保存配置引用），重复创建无性能问题。
    """

    def __init__(self) -> None:
        """初始化工厂，仅保存配置引用。

        get_settings() 内部使用 lru_cache，多次调用返回同一实例，
        不会重复读取 .env 文件。
        """
        self.settings = get_settings()  # Settings 单例，全局共享

    def get_chat_model(self, fast: bool = False) -> BaseChatModel:
        """统一的模型获取入口。

        Args:
            fast: True=轻量模型（偏好提取/搜索），False=主力模型（行程生成）

        Returns:
            配置好的 ChatOpenAI 实例，可直接用于 LangChain 调用。
        """
        if fast:
            return self.create_fast_llm()
        return self.create_llm()

    def create_llm(self) -> BaseChatModel:
        """创建主力模型实例。

        使用 deepseek_model 配置的模型（默认 deepseek-chat/V3），
        设置 temperature=0 确保行程规划输出稳定、可复现。
        streaming=True 开启流式支持，不影响非流式调用。
        """
        return ChatOpenAI(
            model=self.settings.deepseek_model,          # 主力模型名
            base_url=self.settings.deepseek_base_url,    # DeepSeek 兼容端点
            temperature=0,           # 零温度 = 确定性输出，规划场景必须
            streaming=True,          # 开启 SSE 流式能力，不使用时无影响
            api_key=self.settings.deepseek_api_key  # type: ignore[arg-type]
        )

    def create_fast_llm(self) -> BaseChatModel:
        """创建轻量模型实例。

        使用 deepseek_model_fast 配置的模型，当前默认与主力相同。
        后续可通过 .env 切换为更便宜的模型以降低 cost。
        其他参数与主力模型一致。
        """
        return ChatOpenAI(
            model=self.settings.deepseek_model_fast,      # 轻量模型名
            base_url=self.settings.deepseek_base_url,     # 共用同一端点
            temperature=0,            # 轻量任务同样需要稳定输出
            streaming=True,           # 开启 SSE 流式能力
            api_key=self.settings.deepseek_api_key  # type: ignore[arg-type]
        )


# ---- 便捷函数 ----

def get_llm(fast: bool = False) -> BaseChatModel:
    """快捷函数：一行获取 LLM 实例，无需手动管理工厂对象。

    等价于 LLMFactory().get_chat_model(fast)，
    适合在 Graph 节点函数中直接调用。

    使用示例:
        llm = get_llm()            # 主力模型，用于行程生成
        llm = get_llm(fast=True)   # 轻量模型，用于偏好提取和搜索
    """
    return LLMFactory().get_chat_model(fast)
