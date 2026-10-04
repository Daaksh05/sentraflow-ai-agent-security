"""Tests for Pydantic schema validation and integrity."""

import pytest
from pydantic import ValidationError
from app.schemas.action import ActionContext, ActionType, AgentAction
from app.schemas.security import (
    DecisionOutcome,
    IntentAnalysis,
    PolicyDecision,
    SecurityDecision,
)


def test_agent_action_valid():
    action = AgentAction(
        agent_id="agent-001",
        task="Fix failing tests",
        action="READ",
        resource="./tests/test_auth.py",
        parameters={"encoding": "utf-8"},
        context={"user": "developer"},
    )
    assert action.agent_id == "agent-001"
    assert action.action == "READ"
    assert action.resource == "./tests/test_auth.py"
    assert action.parameters["encoding"] == "utf-8"
    assert action.timestamp is not None


def test_agent_action_missing_required_fields():
    with pytest.raises(ValidationError):
        # Missing task, action, resource
        AgentAction(agent_id="agent-001")  # type: ignore


def test_security_decision_schema():
    decision = SecurityDecision(
        decision=DecisionOutcome.ALLOW,
        risk_score=12,
        intent="Read test file to diagnose failing tests",
        reason="Action is within the configured workspace policy",
        analysis_source="placeholder",
    )
    assert decision.decision == DecisionOutcome.ALLOW
    assert decision.risk_score == 12
    assert decision.request_id is not None
    assert decision.evaluated_at is not None


def test_policy_decision_schema():
    policy = PolicyDecision(
        decision=DecisionOutcome.BLOCK,
        reason="Blocked credential access",
        risk_score=95,
        policy_id="SEC-POL-001",
        policy_name="Block Secrets",
    )
    assert policy.decision == DecisionOutcome.BLOCK
    assert policy.risk_score == 95


def test_intent_analysis_schema():
    analysis = IntentAnalysis(
        detected_intent="Inspect environment file",
        confidence=0.92,
        risk_indicators=["sensitive_file_read"],
        risk_score=85,
        explanation="Attempting to read .env secrets file",
    )
    assert analysis.confidence == 0.92
    assert "sensitive_file_read" in analysis.risk_indicators


def test_action_context_schema():
    context = ActionContext(
        agent_id="agent-002",
        task="Deploy service",
        requested_action="EXECUTE",
        target_resource="deploy.sh",
        permissions=["read", "execute"],
    )
    assert context.agent_id == "agent-002"
    assert len(context.permissions) == 2
