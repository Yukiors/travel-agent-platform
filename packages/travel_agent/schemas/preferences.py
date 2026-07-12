"""Pydantic schemas for LLM structured output across all graph nodes."""

import re
from datetime import date, time
from enum import Enum
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# =============================================================================
# Reusable validators
# =============================================================================

def _validate_date_str(v: str) -> str:
    """Validate YYYY-MM-DD format and value."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
        raise ValueError(f"日期格式必须为 YYYY-MM-DD，收到: {v}")
    date.fromisoformat(v)  # raises ValueError if invalid date like 2026-02-30
    return v


def _validate_time_str(v: str) -> str:
    """Validate HH:MM format."""
    if not re.match(r"^\d{2}:\d{2}$", v):
        raise ValueError(f"时间格式必须为 HH:MM，收到: {v}")
    time.fromisoformat(v)
    return v


DateStr = Annotated[str, AfterValidator(_validate_date_str)]
TimeStr = Annotated[str, AfterValidator(_validate_time_str)]


class ActivityType(str, Enum):
    flight = "flight"
    hotel = "hotel"
    attraction = "attraction"
    meal = "meal"
    transit = "transit"


class AttractionType(str, Enum):
    attraction = "attraction"
    meal = "meal"


# =============================================================================
# Preferences extraction — gather_preferences 节点
# =============================================================================

class TravelPreferenceExtraction(BaseModel):
    """从用户消息中提取的旅行偏好（LLM 输出）。

    字段为可选 — LLM 可能无法从消息中提取所有字段，
    gather_preferences 节点会检查必填字段完整性。
    """

    model_config = ConfigDict(extra="forbid")

    destination: str | None = Field(
        default=None,
        min_length=1,
        description="旅行目的地，例如 东京、上海、法国巴黎",
    )

    start_date: DateStr | None = Field(
        default=None,
        description="旅行开始日期，格式为 YYYY-MM-DD",
    )

    end_date: DateStr | None = Field(
        default=None,
        description="旅行结束日期，格式为 YYYY-MM-DD",
    )

    budget: float | None = Field(
        default=None,
        gt=0,
        le=1_000_000,
        description="人均旅行预算，单位为 CNY",
    )

    num_travelers: int = Field(
        default=1,
        ge=1,
        le=10,
        description="出行人数，默认为 1",
    )

    interests: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="旅行兴趣爱好，例如 美食、观光、购物 等",
    )

    clarifying_question: str | None = Field(
        default=None,
        description="信息不足时向用户提出的追问",
    )


class ValidTravelRequest(BaseModel):
    """经过校验的有效旅行请求 — 必填字段已确认完整且合法。"""

    model_config = ConfigDict(extra="forbid")

    destination: str = Field(min_length=1, max_length=100)
    start_date: date
    end_date: date
    budget: float | None = Field(default=None, gt=0, le=1_000_000)
    num_travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_date_range(self) -> "ValidTravelRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date 不能早于 start_date")
        if (self.end_date - self.start_date).days > 60:
            raise ValueError("旅行时间不能超过 60 天")
        return self


# =============================================================================
# Search result schemas — search_flights / search_hotels / search_attractions
# =============================================================================

class FlightOption(BaseModel):
    """单条航班选项。"""
    model_config = ConfigDict(extra="forbid")

    flight_no: str = Field(min_length=1, description="航班号，如 CA1501")
    airline: str = Field(min_length=1, description="航空公司名称")
    departure_time: TimeStr = Field(description="出发时间，如 08:30")
    arrival_time: TimeStr = Field(description="到达时间，如 10:50")
    departure_city: str = Field(min_length=1, description="出发城市")
    arrival_city: str = Field(min_length=1, description="到达城市")
    price: float = Field(gt=0, le=1_000_000, description="票价，CNY")
    stops: int = Field(default=0, ge=0, le=5, description="中转次数")
    duration: str = Field(min_length=1, description="飞行时长，如 2h20m")


class FlightSearchResult(BaseModel):
    """航班搜索完整结果。"""
    model_config = ConfigDict(extra="forbid")
    flights: list[FlightOption] = Field(min_length=1, max_length=10, description="航班选项列表")


class HotelOption(BaseModel):
    """单条酒店选项。"""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, description="酒店名称")
    star: int = Field(ge=1, le=5, description="星级")
    address: str = Field(min_length=1, description="酒店地址")
    price_per_night: float = Field(gt=0, le=1_000_000, description="每晚价格，CNY")
    check_in: TimeStr = Field(description="入住时间，如 15:00")
    check_out: TimeStr = Field(description="退房时间，如 11:00")
    highlights: str = Field(min_length=1, description="酒店亮点")


class HotelSearchResult(BaseModel):
    """酒店搜索完整结果。"""
    model_config = ConfigDict(extra="forbid")
    hotels: list[HotelOption] = Field(min_length=1, max_length=10, description="酒店选项列表")


class AttractionItem(BaseModel):
    """单条景点或餐厅推荐。"""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, description="景点/餐厅名称")
    type: AttractionType = Field(description="类型：attraction 或 meal")
    description: str = Field(min_length=1, description="简要描述")
    recommended_duration: str | None = Field(default=None, description="推荐游玩时长")
    ticket_price: float | None = Field(default=None, ge=0, description="门票价格，免费景点填 0")
    avg_cost: float | None = Field(default=None, ge=0, description="人均消费（餐饮）")
    opening_hours: str | None = Field(default=None, description="营业时间")


class AttractionSearchResult(BaseModel):
    """景点搜索完整结果。"""
    model_config = ConfigDict(extra="forbid")
    attractions: list[AttractionItem] = Field(min_length=1, max_length=30, description="景点和餐厅推荐列表")


# =============================================================================
# Itinerary schemas — build_itinerary 节点
# =============================================================================

class DailyActivity(BaseModel):
    """单日活动安排（对齐 ITINERARY_SYSTEM_PROMPT 的输出格式）。"""
    model_config = ConfigDict(extra="forbid")

    time: TimeStr = Field(description="活动时间，如 08:00")
    type: ActivityType = Field(description="活动类型")
    title: str = Field(min_length=1, description="活动标题，如 前往杭州")
    description: str = Field(min_length=1, description="活动描述")
    cost: float = Field(default=0, ge=0, description="单人费用（CNY），酒店入住/退房填 0")


class DayPlan(BaseModel):
    """单日行程计划。"""
    model_config = ConfigDict(extra="forbid")

    day: int = Field(ge=1, le=60, description="第几天")
    day_date: DateStr = Field(description="日期，YYYY-MM-DD")
    activities: list[DailyActivity] = Field(min_length=1, max_length=20, description="当日活动列表，按时间升序")

    @field_validator("activities")
    @classmethod
    def activities_sorted(cls, v: list[DailyActivity]) -> list[DailyActivity]:
        """Ensure activities are sorted by time."""
        return sorted(v, key=lambda a: a.time)


class ItineraryResult(BaseModel):
    """行程生成完整结果。"""
    model_config = ConfigDict(extra="forbid")
    itinerary: list[DayPlan] = Field(min_length=1, max_length=60, description="每日行程列表")


# =============================================================================
# Finalize schemas — finalize_plan 节点
# =============================================================================

class BudgetBreakdown(BaseModel):
    """费用明细（对齐 FINALIZE_SYSTEM_PROMPT 的 breakdown 字段）。"""
    model_config = ConfigDict(extra="forbid")

    flights: float = Field(default=0, ge=0, description="航班费用合计")
    hotels: float = Field(default=0, ge=0, description="酒店费用合计")
    attractions: float = Field(default=0, ge=0, description="景点门票合计")
    meals: float = Field(default=0, ge=0, description="餐饮费用合计")


class BudgetAnalysis(BaseModel):
    """预算分析（对齐 FINALIZE_SYSTEM_PROMPT）。"""
    model_config = ConfigDict(extra="forbid")

    total_per_person: float = Field(gt=0, description="单人总费用")
    breakdown: BudgetBreakdown = Field(description="费用明细")
    within_budget: bool = Field(description="是否在预算内")


class FinalizedPlan(BaseModel):
    """最终确认的旅行计划（对齐 FINALIZE_SYSTEM_PROMPT）。"""
    model_config = ConfigDict(extra="forbid")

    status: str = Field(default="confirmed", pattern=r"^confirmed$", description="固定为 confirmed")
    summary: str = Field(min_length=1, description="行程摘要，1-2 句概述")
    highlights: list[str] = Field(min_length=1, max_length=10, description="按天列出行程亮点")
    tips: list[str] = Field(min_length=1, max_length=10, description="实用旅行建议")
    budget_analysis: BudgetAnalysis = Field(description="预算分析")
    issues: list[str] = Field(default_factory=list, max_length=20, description="发现的问题列表")
