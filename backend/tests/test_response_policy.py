"""Focused tests for adaptive risk-based response decisions."""

import logging

import pytest
from pydantic import ValidationError

from app.ai.base import ModelProvider
from app.core.config import Settings
from app.schemas.action import AgentAction
from app.schemas.security import DecisionOutcome, IntentAnalysis
from app.security.interceptor import DefaultActionInterceptor
from app.security.response_policy import AdaptiveResponsePolicy


class FixedRiskProvider(ModelProvider):
    def __init__(self, risk_score: int):
        self.risk_score = risk_score
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "test"

    @property
    def model_name(self) -> str:
        return "test-model"

    async def analyze_intent(self, action, context=None):
        self.call_count += 1
        return IntentAnalysis(
            detected_intent="Test intent",
            confidence=1.0,
            risk_score=self.risk_score,
            explanation="Test risk assessment",
            model_provider=self.provider_name,
            model_name=self.model_name,
        )


class FailingProvider(FixedRiskProvider):
    async def analyze_intent(self, action, context=None):
        raise RuntimeError("provider unavailable")


def make_action(resource: str = "src/module.py") -> AgentAction:
    return AgentAction(
        agent_id="agent-test",
        task="Run a test action",
        action="READ",
        resource=resource,
    )


@pytest.mark.parametrize(
    ("risk_score", "expected"),
    [
        (0, DecisionOutcome.ALLOW),
        (29, DecisionOutcome.ALLOW),
        (30, DecisionOutcome.REQUIRE_APPROVAL),
        (59, DecisionOutcome.REQUIRE_APPROVAL),
        (60, DecisionOutcome.ESCALATE),
        (79, DecisionOutcome.ESCALATE),
        (80, DecisionOutcome.BLOCK),
        (100, DecisionOutcome.BLOCK),
    ],
)
def test_each_response_threshold(risk_score, expected):
    response, rationale = AdaptiveResponsePolicy().recommend(risk_score)

    assert response == expected
    assert str(risk_score) in rationale


def test_custom_response_thresholds():
    policy = AdaptiveResponsePolicy(
        require_approval_threshold=20,
        escalate_threshold=45,
        block_threshold=90,
    )

    assert policy.recommend(19)[0] == DecisionOutcome.ALLOW
    assert policy.recommend(20)[0] == DecisionOutcome.REQUIRE_APPROVAL
    assert policy.recommend(45)[0] == DecisionOutcome.ESCALATE
    assert policy.recommend(90)[0] == DecisionOutcome.BLOCK


@pytest.mark.parametrize(
    "values",
    [
        {
            "REQUIRE_APPROVAL_RISK_THRESHOLD": 60,
            "ESCALATE_RISK_THRESHOLD": 60,
            "BLOCK_RISK_THRESHOLD": 80,
        },
        {
            "REQUIRE_APPROVAL_RISK_THRESHOLD": 30,
            "ESCALATE_RISK_THRESHOLD": 90,
            "BLOCK_RISK_THRESHOLD": 80,
        },
        {
            "REQUIRE_APPROVAL_RISK_THRESHOLD": -1,
            "ESCALATE_RISK_THRESHOLD": 60,
            "BLOCK_RISK_THRESHOLD": 80,
        },
        {
            "REQUIRE_APPROVAL_RISK_THRESHOLD": 30,
            "ESCALATE_RISK_THRESHOLD": 60,
            "BLOCK_RISK_THRESHOLD": 101,
        },
    ],
)
def test_invalid_configured_thresholds_are_rejected(values):
    with pytest.raises(ValidationError):
        Settings(**values)


@pytest.mark.parametrize(
    "thresholds",
    [(30, 30, 80), (30, 90, 80), (-1, 60, 80), (30, 60, 101)],
)
def test_invalid_response_policy_thresholds_are_rejected(thresholds):
    with pytest.raises(ValueError):
        AdaptiveResponsePolicy(*thresholds)


@pytest.mark.asyncio
async def test_mandatory_policy_block_precedes_ai_response():
    provider = FixedRiskProvider(0)
    interceptor = DefaultActionInterceptor(model_provider=provider)

    decision = await interceptor.intercept(make_action(".env"))

    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.recommended_response == DecisionOutcome.BLOCK
    assert decision.risk_score == 95
    assert "Mandatory deterministic BLOCK" in decision.policy_rationale
    assert provider.call_count == 0


@pytest.mark.asyncio
async def test_ai_high_risk_maps_to_block():
    interceptor = DefaultActionInterceptor(model_provider=FixedRiskProvider(85))

    decision = await interceptor.intercept(make_action())

    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.recommended_response == DecisionOutcome.BLOCK
    assert decision.risk_score == 85


@pytest.mark.asyncio
async def test_ai_provider_failure_uses_conservative_approval_fallback(caplog):
    interceptor = DefaultActionInterceptor(model_provider=FailingProvider(0))

    with caplog.at_level(logging.INFO, logger="sentraflow.security"):
        decision = await interceptor.intercept(make_action())

    assert decision.risk_score == 50
    assert decision.decision == DecisionOutcome.REQUIRE_APPROVAL
    assert decision.recommended_response == DecisionOutcome.REQUIRE_APPROVAL
    assert decision.analysis_source == "policy+ai_fallback"
    assert "AI intent analysis failed" in decision.policy_rationale
    event = next(
        record.security_event
        for record in caplog.records
        if hasattr(record, "security_event")
    )
    assert event["decision"] == "REQUIRE_APPROVAL"
    assert event["risk_score"] == 50
    assert event["request_id"] == decision.request_id
    assert event["response_mode"] == "decision"
    assert event["response_outcome"] == "decision_returned_to_caller"
    assert event["policy_rationale"] == decision.policy_rationale


@pytest.mark.asyncio
async def test_ai_failure_fallback_respects_custom_approval_threshold():
    interceptor = DefaultActionInterceptor(
        model_provider=FailingProvider(0),
        response_policy=AdaptiveResponsePolicy(70, 90, 95),
    )

    decision = await interceptor.intercept(make_action())

    assert decision.risk_score == 70
    assert decision.decision == DecisionOutcome.REQUIRE_APPROVAL


@pytest.mark.asyncio
async def test_audit_only_records_recommendation_without_returning_it_as_decision():
    interceptor = DefaultActionInterceptor(
        model_provider=FixedRiskProvider(90),
        response_mode="audit_only",
    )

    decision = await interceptor.intercept(make_action())

    assert decision.decision == DecisionOutcome.ALLOW
    assert decision.recommended_response == DecisionOutcome.BLOCK
    assert decision.response_mode == "audit_only"
    assert decision.response_outcome == "recommendation_recorded_only"
    assert decision.policy_rationale


@pytest.mark.asyncio
async def test_audit_only_does_not_suppress_mandatory_policy_block():
    interceptor = DefaultActionInterceptor(
        model_provider=FixedRiskProvider(0),
        response_mode="audit_only",
    )

    decision = await interceptor.intercept(make_action(".env"))

    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.recommended_response == DecisionOutcome.BLOCK
    assert decision.response_outcome == "mandatory_policy_block_returned"
