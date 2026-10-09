"""Security evaluation endpoints for agent actions and session trajectory analysis."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.action import AgentAction, BatchAgentActionRequest
from app.schemas.security import (
    BatchSecurityDecisionResponse,
    BehaviorAnalysis,
    SecurityDecision,
)
from app.security.behavior_monitor import behavior_monitor
from app.services.security_service import SecurityService, security_service

router = APIRouter(tags=["Security Evaluation"])


@router.post(
    "/analyze",
    response_model=SecurityDecision,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Agent Action",
    description=(
        "Evaluates an autonomous AI agent action against deterministic security "
        "policies, AI intent analysis, and behavioral trajectory monitoring. "
        "Returns an ALLOW, REQUIRE_APPROVAL, ESCALATE, or BLOCK decision. "
        "This evaluation does not itself pause or terminate an agent, grant "
        "approval, or change permissions."
    ),
)
async def analyze_action(
    action: AgentAction,
    service: SecurityService = Depends(lambda: security_service),
) -> SecurityDecision:
    """Analyze an agent action and return its security decision and telemetry."""
    decision = await service.evaluate_action(action, action.action_context)
    return decision


@router.post(
    "/analyze/batch",
    response_model=BatchSecurityDecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate Batch of Agent Actions",
    description=(
        "Evaluates a sequence or plan of multiple autonomous agent actions, "
        "returning individual decisions and aggregate risk metrics."
    ),
)
async def analyze_action_batch(
    batch_request: BatchAgentActionRequest,
    service: SecurityService = Depends(lambda: security_service),
) -> BatchSecurityDecisionResponse:
    """Evaluate multiple planned agent actions."""
    return await service.evaluate_batch(batch_request)


@router.get(
    "/sessions/{session_id}/trajectory",
    response_model=BehaviorAnalysis,
    status_code=status.HTTP_200_OK,
    summary="Get Session Behavioral Trajectory",
    description=(
        "Retrieves the multi-action behavioral trajectory and risk assessment "
        "for a specific agent session."
    ),
)
async def get_session_trajectory(session_id: str) -> BehaviorAnalysis:
    """Return behavioral trajectory features and risk evaluation for a session."""
    analysis = behavior_monitor.get_session_trajectory(session_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No active trajectory history found for session '{session_id}'"
            ),
        )

    return analysis


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK,
    summary="Reset Session Trajectory",
    description="Resets recorded behavioral action history for an agent session.",
)
async def reset_session_trajectory(session_id: str):
    """Clear history for the given agent session."""
    success = behavior_monitor.reset_session(session_id)

    return {
        "status": "reset",
        "session_id": session_id,
        "found": success,
    }