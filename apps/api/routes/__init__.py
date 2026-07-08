"""API route definitions."""

from fastapi import APIRouter

from apps.api.routes import travel

router = APIRouter()
router.include_router(travel.router, prefix="/travel", tags=["travel"])
