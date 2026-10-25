"""Unit tests for AI Policy Synthesizer and Red Team Adversarial Arena."""

import pytest
from app.schemas.action import AgentAction
from app.schemas.redteam import RedTeamRunRequest
from app.schemas.security import DecisionOutcome
from app.schemas.synthesizer import PolicySynthesizeRequest
from app.services.redteam_service import redteam_service
from app.services.synthesizer_service import policy_synthesizer
from app.services.security_service import security_service


@pytest.mark.asyncio
async def test_policy_synthesizer_creates_valid_rule():
    request = PolicySynthesizeRequest(
        prompt="Block all attempts to execute python scripts from /tmp directory",
        auto_activate=True,
    )
    initial_rule_count = len(security_service.policy_engine.rules)

    response = await policy_synthesizer.synthesize(request)

    assert response.success is True
    assert response.rule is not None
    assert response.rule.decision == DecisionOutcome.BLOCK
    assert "tmp" in response.rule.resource_pattern
    assert response.activated is True
    assert response.total_active_rules == initial_rule_count + 1
    assert response.validation_status in ["VALID_REGEX", "ESCAPED_FALLBACK"]


@pytest.mark.asyncio
async def test_synthesized_rule_enforces_immediately():
    """Verify that a synthesized rule immediately blocks matching agent actions."""
    request = PolicySynthesizeRequest(
        prompt="Block any write operation to /var/secrets/ directory",
        auto_activate=True,
    )
    await policy_synthesizer.synthesize(request)

    action = AgentAction(
        agent_id="test-agent",
        task="Write temporary credentials",
        action="WRITE",
        resource="/var/secrets/token.txt",
    )
    decision = await security_service.evaluate_action(action)
    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.risk_score >= 80


def test_redteam_scenarios_listing():
    scenarios = redteam_service.get_scenarios()
    assert len(scenarios) >= 4
    for sc in scenarios:
        assert sc.id.startswith("SCENARIO-")
        assert sc.owasp_tag.startswith("OWASP")
        assert len(sc.name) > 0


@pytest.mark.asyncio
async def test_redteam_run_blocks_adversarial_scenario():
    request = RedTeamRunRequest(scenario_id="SCENARIO-ADV-001")
    result = await redteam_service.run_scenario(request)

    assert result.attack_thwarted is True
    assert result.decision.decision == DecisionOutcome.BLOCK
    assert "Phase 1" in result.defense_stage or "Policy" in result.defense_stage
