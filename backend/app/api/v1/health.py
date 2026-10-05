"""Health check endpoints."""

from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str = Field(default="healthy", json_schema_extra={"example": "healthy"})
    service: str = Field(default="sentraflow-backend", json_schema_extra={"example": "sentraflow-backend"})
    version: str = Field(default=settings.VERSION, json_schema_extra={"example": "0.1.0"})
    environment: str = Field(default=settings.ENVIRONMENT, json_schema_extra={"example": "development"})
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@router.get("/health", response_model=HealthResponse, summary="API v1 Health Check")
async def health_check_v1() -> HealthResponse:
    """Returns the operational status of the SentraFlow backend service."""
    return HealthResponse()
