"""Main API v1 router aggregator."""

from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.security import router as security_router
from app.api.v1.synthesizer import router as synthesizer_router
from app.api.v1.redteam import router as redteam_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(security_router)
api_router.include_router(synthesizer_router)
api_router.include_router(redteam_router)

__all__ = ["api_router"]
