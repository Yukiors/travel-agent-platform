import json
import random
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """所有工具的抽象基类。Mock 和真实 API 工具都需实现此接口。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """工具唯一标识，如 'flights'、'hotels'。"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述，用于发现和日志。"""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """执行工具的核心方法。返回工具特定结果，无结果时返回空列表而非 None。"""
        ...

    async def health_check(self) -> bool:
        """可选：检查工具可用性。默认始终返回 True。"""
        return True


class BaseMockTool(BaseTool):
    """所有 Mock 工具的基类，提供种子确定性选择逻辑。

    子类只需设置 domain 和 description 类属性，实现 execute() 方法。
    name 属性自动从 domain 派生，无需手动设置。
    """

    domain: str = ""       # 子类设置，对应数据域名称（如 "hotels"）
    description: str = ""  # 子类设置，工具描述文本

    @property
    def name(self) -> str:
        return self.domain

    async def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError("子类必须实现 execute 方法")

    def _get_seed(self, **params: object) -> int:
        """从请求参数生成确定性种子。对参数排序确保相同输入产生相同种子。"""
        key = json.dumps(params, sort_keys=True, ensure_ascii=False, default=str)
        return hash(key) & 0x7FFFFFFF

    def _select_options(self, pool: list[dict], seed: int, count: int = 3) -> list[dict]:
        """从数据池中确定性选择 count 条记录（不修改原始 pool）。"""
        if not pool:
            return []
        rng = random.Random(seed)
        copied = pool.copy()
        rng.shuffle(copied)
        return copied[:count]
