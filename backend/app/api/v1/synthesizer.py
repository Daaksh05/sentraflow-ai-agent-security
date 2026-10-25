"""FastAPI endpoints for AI Policy Synthesizer (Natural Language to Zero-Trust Policy)."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from app.schemas.synthesizer import PolicySynthesizeRequest, PolicySynthesizeResponse
from app.services.synthesizer_service import PolicySynthesizerService, policy_synthesizer
from app.services.security_service import security_service

router = APIRouter(prefix="/policies", tags=["AI Policy Synthesizer"])


@router.post(
    "/synthesize",
    response_model=PolicySynthesizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize Zero-Trust Policy from Natural Language",
    description=(
        "Translates plain-English security requirements into production-grade "
        "deterministic regex policy rules using NVIDIA Nemotron 3.5 Bolt. "
        "Optionally hot-reloads the synthesized rule directly into the active kernel."
    ),
)
async def synthesize_policy(
    request: PolicySynthesizeRequest,
    service: PolicySynthesizerService = Depends(lambda: policy_synthesizer),
) -> PolicySynthesizeResponse:
    """Compile natural language into a zero-trust PolicyRule and optionally activate it."""
    return await service.synthesize(request)


@router.get(
    "/active",
    response_model=List[Dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List Active Policy Rules",
    description="Returns all active deterministic and synthesized rules currently enforcing boundaries.",
)
def get_active_rules() -> List[Dict[str, Any]]:
    """Return all active policy rules."""
    return security_service.policy_engine.get_active_rules()
