"""Schemas for Security Policies, Intent Analysis, and Security Decisions."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Literal, Optional
import uuid
from pydantic import BaseModel, Field


class DecisionOutcome(str, Enum):
    """The final actionable decision for an intercepted agent action."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    ESCALATE = "ESCALATE"


class PolicyDecision(BaseModel):
    """Deterministic evaluation outcome from the SentraFlow Policy Engine."""
    decision: DecisionOutcome = Field(..., description="ALLOW or BLOCK decision based on static policy rules")
    reason: str = Field(..., description="Explanation of why the rule passed or failed")
    risk_score: int = Field(..., ge=0, le=100, description="Risk score calculated by policy engine (0-100)")
    policy_id: Optional[str] = Field(default=None, description="Identifier of the matching policy rule")
    policy_name: Optional[str] = Field(default=None, description="Human-readable name of the evaluated policy")
    rule_matched: Optional[str] = Field(default=None, description="The specific rule condition that triggered")


class IntentAnalysis(BaseModel):
    """Semantic intent evaluation and risk classification produced by AI (e.g. NVIDIA Nemotron)."""
    detected_intent: str = Field(..., description="Understood agent intent extracted from prompt, context, and action")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence in its intent understanding (0.0 - 1.0)")
    risk_indicators: List[str] = Field(default_factory=list, description="Specific risk flags identified (e.g., credential_access, destructive_write)")
    risk_score: int = Field(default=0, ge=0, le=100, description="AI estimated risk score (0-100)")
    explanation: str = Field(..., description="Detailed semantic rationale for the intent and risk assessment")
    model_provider: str = Field(default="nemotron", description="Model provider identifier")
    model_name: Optional[str] = Field(default=None, description="Specific model identifier used")


class SecurityDecision(BaseModel):
    """Unified security decision combining deterministic policy rules and AI intent analysis."""
    decision: DecisionOutcome = Field(..., description="Final response decision returned by the security evaluation", examples=["ALLOW"])
    risk_score: int = Field(..., ge=0, le=100, description="Composite risk score from 0 (safe) to 100 (critical)", examples=[12])
    intent: str = Field(..., description="Synthesized understanding of the agent's intent", examples=["Read test file to diagnose failing tests"])
    reason: str = Field(..., description="Auditable justification for the final decision", examples=["Action is within the configured workspace policy"])
    analysis_source: str = Field(default="placeholder", description="Source of the security evaluation (e.g., 'placeholder', 'policy+nemotron', 'policy_only')", examples=["placeholder"])
    response_mode: Literal["decision", "audit_only"] = Field(
        default="decision",
        description="Whether the adaptive recommendation is returned as the decision or recorded for audit only",
    )
    response_outcome: str = Field(
        default="decision_returned_to_caller",
        description="What the evaluation returned; this does not claim runtime enforcement",
    )
    recommended_response: Optional[DecisionOutcome] = Field(
        default=None,
        description="Risk-based response recommendation, which may differ from decision in audit-only mode",
    )
    policy_rationale: Optional[str] = Field(
        default=None,
        description="Rationale for the adaptive response recommendation",
    )
    
    # Detailed sub-evaluation metadata
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Traceable unique identifier for the evaluation event")
    policy_decision: Optional[PolicyDecision] = Field(default=None, description="Underlying policy engine decision")
    intent_analysis: Optional[IntentAnalysis] = Field(default=None, description="Underlying AI intent analysis")
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Evaluation timestamp")
