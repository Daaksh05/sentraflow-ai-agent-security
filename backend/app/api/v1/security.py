"""Security evaluation endpoints for agent actions."""

from fastapi import APIRouter, Depends, status
from app.schemas.action import AgentAction
from app.schemas.security import SecurityDecision
from app.services.security_service import SecurityService, security_service

router = APIRouter(prefix="/analyze", tags=["Security Evaluation"])


@router.post(
    "",
    response_model=SecurityDecision,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Agent Action",
    description="Evaluates an autonomous AI agent action against security policies and AI intent analysis, returning an ALLOW or BLOCK decision.",
)
async def analyze_action(
    action: AgentAction,
    service: SecurityService = Depends(lambda: security_service),
) -> SecurityDecision:
    """Interception endpoint: Analyzes requested agent action and returns structured decision."""
    decision = await service.evaluate_action(action)
    return decision
