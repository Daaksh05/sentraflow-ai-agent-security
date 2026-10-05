"""Unit tests for ENFORCE vs AUDIT_ONLY modes in SentraFlow."""

import pytest
from app.schemas.action import AgentAction
from app.schemas.security import DecisionOutcome
from app.security.interceptor import DefaultActionInterceptor
from app.security.policy_engine import PolicyEngine


@pytest.mark.asyncio
async def test_enforce_mode_blocks_dangerous_action():
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        enforcement_mode="ENFORCE",
    )
    action = AgentAction(
        agent_id="agent-01",
        task="Read credentials",
        action="READ",
        resource=".env",
    )
    decision = await interceptor.intercept(action)
    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.risk_score >= 90
    assert decision.enforcement_mode == "ENFORCE"


@pytest.mark.asyncio
async def test_audit_only_mode_logs_and_permits_with_audit_tag():
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        enforcement_mode="AUDIT_ONLY",
    )
    action = AgentAction(
        agent_id="agent-01",
        task="Read credentials in observation mode",
        action="READ",
        resource=".env",
    )
    decision = await interceptor.intercept(action)
    
    # In AUDIT_ONLY mode, execution is permitted but telemetry captures the full risk and audit warning
    assert decision.decision == DecisionOutcome.ALLOW
    assert decision.risk_score >= 90
    assert "AUDIT_ONLY" in decision.reason
    assert "audit_override" in decision.analysis_source
    assert decision.enforcement_mode == "AUDIT_ONLY"
