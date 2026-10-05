"""Security evaluation endpoints for agent actions."""

from fastapi import APIRouter, Depends, status
from app.schemas.action import AgentAction, BatchAgentActionRequest
from app.schemas.security import BatchSecurityDecisionResponse, SecurityDecision
from app.services.security_service import SecurityService, security_service

router = APIRouter(prefix="/analyze", tags=["Security Evaluation"])


@router.post(
    "",
    response_model=SecurityDecision,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Agent Action",
    description="Evaluates an autonomous AI agent action against deterministic security policies and AI intent analysis, returning an ALLOW or BLOCK decision.",
)
async def analyze_action(
    action: AgentAction,
    service: SecurityService = Depends(lambda: security_service),
) -> SecurityDecision:
    """Interception endpoint: Analyzes requested agent action and returns structured decision."""
    decision = await service.evaluate_action(action, action.action_context)
    return decision


@router.post(
    "/batch",
    response_model=BatchSecurityDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Batch of Agent Actions",
    description="Evaluates a sequence or plan of multiple autonomous agent actions, returning individual decisions and aggregate risk metrics.",
)
async def analyze_action_batch(
    batch_request: BatchAgentActionRequest,
    service: SecurityService = Depends(lambda: security_service),
) -> BatchSecurityDecisionResponse:
    """Batch interception endpoint for evaluating multi-step agent plans."""
    return await service.evaluate_batch(batch_request)
