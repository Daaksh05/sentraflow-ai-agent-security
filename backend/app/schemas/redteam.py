"""Pydantic schemas for the Red Team vs. Blue Team Adversarial Arena."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.action import AgentAction
from app.schemas.security import SecurityDecision


class AttackScenario(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    owasp_tag: str
    mitre_tactic: str
    description: str
    adversarial_technique: str
    action: AgentAction


class RedTeamRunRequest(BaseModel):
    scenario_id: Optional[str] = Field(default=None, description="Pre-configured attack scenario ID")
    custom_action: Optional[AgentAction] = Field(default=None, description="Custom adversarial agent action")


class RedTeamRunResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    owasp_tag: str
    mitre_tactic: str
    attack_technique: str
    action_submitted: AgentAction
    decision: SecurityDecision
    attack_thwarted: bool
    defense_stage: str
    explanation: str
