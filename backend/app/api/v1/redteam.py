"""FastAPI endpoints for Red Team vs. Blue Team Adversarial Arena."""

from typing import List
from fastapi import APIRouter, Depends, status
from app.schemas.redteam import AttackScenario, RedTeamRunRequest, RedTeamRunResponse
from app.services.redteam_service import RedTeamService, redteam_service

router = APIRouter(prefix="/redteam", tags=["Red Team Adversarial Arena"])


@router.get(
    "/scenarios",
    response_model=List[AttackScenario],
    status_code=status.HTTP_200_OK,
    summary="List Adversarial Attack Scenarios",
    description="Returns curated advanced adversarial attack vectors targeting autonomous AI agents.",
)
def get_attack_scenarios(
    service: RedTeamService = Depends(lambda: redteam_service),
) -> List[AttackScenario]:
    """Retrieve all pre-configured red team exploit scenarios."""
    return service.get_scenarios()


@router.post(
    "/run",
    response_model=RedTeamRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Launch Adversarial Exploit & Analyze Defense",
    description=(
        "Simulates an adversarial attack against SentraFlow and evaluates "
        "whether Phase 1 (Policy), Phase 2 (NVIDIA Nemotron 3.5), or Phase 3 (Trajectory) "
        "halts the attack."
    ),
)
async def run_attack_scenario(
    request: RedTeamRunRequest,
    service: RedTeamService = Depends(lambda: redteam_service),
) -> RedTeamRunResponse:
    """Launch an adversarial exploit scenario and return defense telemetry."""
    return await service.run_scenario(request)
