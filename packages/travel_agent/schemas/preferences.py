"""Pydantic schemas for LLM structured output across all graph nodes."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


# =============================================================================
# Preferences extraction — gather_preferences 节点
# =============================================================================

class TravelPreferenceExtraction(BaseModel):
    """从用户消息中提取的旅行偏好（LLM 输出）。

    字段为可选 — LLM 可能无法从消息中提取所有字段，
    gather_preferences 节点会检查必填字段完整性。
    """

    model_config = ConfigDict(extra="ignore")

    destination: str | None = Field(
        default=None,
        description="旅行目的地，例如 东京、上海、法国巴黎",
    )

    start_date: str | None = Field(
        default=None,
        description="旅行开始日期，格式为 YYYY-MM-DD",
    )

    end_date: str | None = Field(
        default=None,
        description="旅行结束日期，格式为 YYYY-MM-DD",
    )

    budget: float | None = Field(
        default=None,
        gt=0,
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
        description="旅行兴趣爱好，例如 美食、观光、购物 等",
    )

    clarifying_question: str | None = Field(
        default=None,
        description="信息不足时向用户提出的追问",
    )


class ValidTravelRequest(BaseModel):
    """经过校验的有效旅行请求 — 必填字段已确认完整且合法。"""

    model_config = ConfigDict(extra="forbid")

    destination: str = Field(min_length=1)
    start_date: date
    end_date: date
    budget: float | None = Field(default=None, gt=0)
    num_travelers: int = Field(default=1, ge=1, le=20)
    interests: list[str] = Field(default_factory=list)

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
    model_config = ConfigDict(extra="ignore")
    flight_no: str = Field(description="航班号，如 CA1501")
    airline: str = Field(description="航空公司名称")
    departure_time: str = Field(description="出发时间，如 08:30")
    arrival_time: str = Field(description="到达时间，如 10:50")
    departure_city: str = Field(description="出发城市")
    arrival_city: str = Field(description="到达城市")
    price: float = Field(gt=0, description="票价，CNY")
    stops: int = Field(default=0, ge=0, description="中转次数")
    duration: str = Field(description="飞行时长，如 2h20m")


class FlightSearchResult(BaseModel):
    """航班搜索完整结果。"""
    model_config = ConfigDict(extra="ignore")
    flights: list[FlightOption] = Field(description="航班选项列表")


class HotelOption(BaseModel):
    """单条酒店选项。"""
    model_config = ConfigDict(extra="ignore")
    name: str = Field(description="酒店名称")
    star: int = Field(ge=1, le=5, description="星级")
    address: str = Field(description="酒店地址")
    price_per_night: float = Field(gt=0, description="每晚价格，CNY")
    check_in: str = Field(description="入住时间，如 15:00")
    check_out: str = Field(description="退房时间，如 11:00")
    highlights: str = Field(description="酒店亮点")


class HotelSearchResult(BaseModel):
    """酒店搜索完整结果。"""
    model_config = ConfigDict(extra="ignore")
    hotels: list[HotelOption] = Field(description="酒店选项列表")


class AttractionItem(BaseModel):
    """单条景点或餐厅推荐。"""
    model_config = ConfigDict(extra="ignore")
    name: str = Field(description="景点/餐厅名称")
    type: str = Field(description="类型：attraction 或 meal")
    description: str = Field(description="简要描述")
    recommended_duration: str | None = Field(default=None, description="推荐游玩时长")
    ticket_price: float | None = Field(default=None, description="门票价格")
    avg_cost: float | None = Field(default=None, description="人均消费（餐饮）")
    opening_hours: str | None = Field(default=None, description="营业时间")


class AttractionSearchResult(BaseModel):
    """景点搜索完整结果。"""
    model_config = ConfigDict(extra="ignore")
    attractions: list[AttractionItem] = Field(description="景点和餐厅推荐列表")


# =============================================================================
# Itinerary schemas — build_itinerary 节点
# =============================================================================

class DailyActivity(BaseModel):
    """单日活动安排。"""
    model_config = ConfigDict(extra="ignore")
    time: str = Field(description="活动时间，如 08:00")
    activity: str = Field(description="活动名称")
    location: str | None = Field(default=None, description="活动地点")
    type: str = Field(description="活动类型：flight/hotel/attraction/meal/transit")
    estimated_cost: float | None = Field(default=None, description="预估费用")
    notes: str | None = Field(default=None, description="备注")


class DayPlan(BaseModel):
    """单日行程计划。"""
    model_config = ConfigDict(extra="ignore")
    day: int = Field(description="第几天")
    date: str = Field(description="日期，YYYY-MM-DD")
    theme: str | None = Field(default=None, description="当日主题")
    activities: list[DailyActivity] = Field(description="当日活动列表")


class ItineraryResult(BaseModel):
    """行程生成完整结果。"""
    model_config = ConfigDict(extra="ignore")
    itinerary: list[DayPlan] = Field(description="每日行程列表")


# =============================================================================
# Finalize schemas — finalize_plan 节点
# =============================================================================

class BudgetItem(BaseModel):
    """预算明细项。"""
    model_config = ConfigDict(extra="ignore")
    category: str = Field(description="费用类别，如 交通、住宿、餐饮、门票")
    amount: float = Field(gt=0, description="金额，CNY")
    detail: str | None = Field(default=None, description="明细说明")


class BudgetAnalysis(BaseModel):
    """预算分析。"""
    model_config = ConfigDict(extra="ignore")
    total: float = Field(description="总费用")
    items: list[BudgetItem] = Field(default_factory=list, description="费用明细")


class FinalizedPlan(BaseModel):
    """最终确认的旅行计划。"""
    model_config = ConfigDict(extra="ignore")

    summary: str = Field(description="行程摘要，1-2 句概述")
    highlights: list[str] = Field(default_factory=list, description="行程亮点")
    tips: list[str] = Field(default_factory=list, description="实用建议")
    budget_analysis: BudgetAnalysis | None = Field(default=None, description="预算分析")
    issues: list[str] = Field(default_factory=list, description="注意事项")
