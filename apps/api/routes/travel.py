"""Travel planning API routes."""

from fastapi import APIRouter, Depends

from apps.api.schemas.travel import (
    TravelPlanRequest,
    TravelPlanResponse,
)

router = APIRouter()


@router.post("/plan", response_model=TravelPlanResponse)
async def create_travel_plan(request: TravelPlanRequest) -> TravelPlanResponse:
    """Generate a travel plan based on user preferences."""
    raise NotImplementedError("Travel planning endpoint not yet implemented")


@router.get("/plan/{plan_id}", response_model=TravelPlanResponse)
async def get_travel_plan(plan_id: str) -> TravelPlanResponse:
    """Retrieve an existing travel plan by ID."""
    raise NotImplementedError("Travel plan retrieval not yet implemented")
