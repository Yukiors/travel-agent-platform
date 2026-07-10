"""Travel-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TravelPreference(BaseModel):
    """User travel preferences."""

    destination: str = Field(..., description="Target destination")
    start_date: str = Field(..., description="Travel start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Travel end date (YYYY-MM-DD)")
    budget: Optional[float] = Field(None, description="Total budget in CNY")
    interests: list[str] = Field(default_factory=list, description="Travel interests")
    num_travelers: int = Field(default=1, ge=1, description="Number of travelers")


class TravelPlanRequest(BaseModel):
    """Request to generate a travel plan."""

    preferences: TravelPreference
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")


class TravelPlanResponse(BaseModel):
    """Response containing a travel plan."""

    plan_id: str
    destination: str
    itinerary: list[dict]
    final_plan: dict
    total_budget_estimate: float
    created_at: datetime


class TravelPlanStreamResponse(BaseModel):
    """Stream response for travel plan generation."""

    event_type: str
    data: dict
