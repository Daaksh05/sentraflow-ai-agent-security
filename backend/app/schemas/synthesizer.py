"""Pydantic schemas for AI Policy Synthesizer (Natural Language to Zero-Trust Policy)."""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.security import DecisionOutcome


class PolicySynthesizeRequest(BaseModel):
    prompt: str = Field(
        ...,
        description="Natural language description of desired policy constraint or allowance",
        min_length=5,
        examples=["Block all attempts to execute python scripts from /tmp and forbid writes to /etc/"],
    )
    auto_activate: bool = Field(
        default=True,
        description="Automatically hot-reload the synthesized rule into the active PolicyEngine",
    )


class SynthesizedRule(BaseModel):
    rule_id: str
    name: str
    resource_pattern: str
    action_pattern: str
    decision: DecisionOutcome
    risk_score: int
    reason: str
    explanation: Optional[str] = None


class PolicySynthesizeResponse(BaseModel):
    success: bool
    prompt: str
    rule: SynthesizedRule
    activated: bool
    total_active_rules: int
    model_name: str
    validation_status: str
