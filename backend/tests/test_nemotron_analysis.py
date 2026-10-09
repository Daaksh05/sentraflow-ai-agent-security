"""Unit and integration tests for Nemotron contextual AI intent and risk analysis."""

import json
from pathlib import Path
import pytest
import httpx
from app.ai.nemotron import MockModelProvider, NemotronProvider
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import DecisionOutcome, RiskLevel
from app.security.interceptor import DefaultActionInterceptor
from app.security.policy_engine import PolicyEngine


@pytest.fixture
def test_cases():
    fixture_path = Path(__file__).parent / "fixtures" / "contextual_security_cases.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_mock_provider_evaluates_dataset(test_cases):
    provider = MockModelProvider()
    for case in test_cases:
        action = AgentAction(
            agent_id="agent-dataset",
            task=case["task"],
            action=case["action"],
            resource=case["resource"],
        )
        analysis = await provider.analyze_intent(action)
        assert analysis.risk_level.value == case["expected_risk_level"], (
            f"Failed on case {case['id']} ({case['name']}): expected {case['expected_risk_level']}, got {analysis.risk_level.value}"
        )
        if "expected_min_task_relevance" in case:
            assert analysis.task_relevance >= case["expected_min_task_relevance"]
        if "expected_max_task_relevance" in case:
            assert analysis.task_relevance <= case["expected_max_task_relevance"]


@pytest.mark.asyncio
async def test_nemotron_provider_fallback_on_missing_key():
    provider = NemotronProvider(api_key="")
    action = AgentAction(
        agent_id="agent-01",
        task="Read source",
        action="READ",
        resource="./src/main.py",
    )
    analysis = await provider.analyze_intent(action)
    assert analysis.risk_level == RiskLevel.LOW
    assert analysis.confidence >= 0.70
    assert "placeholder fallback" in analysis.explanation


@pytest.mark.asyncio
async def test_nemotron_provider_parses_valid_json_response(monkeypatch):
    mock_response_content = {
        "detected_intent": "Inspect authentication test suite",
        "task_relevance": 0.96,
        "risk_score": 14,
        "risk_level": "LOW",
        "confidence": 0.98,
        "risk_indicators": [],
        "explanation": "Action aligns directly with debugging auth tests.",
        "recommended_action": "ALLOW",
    }

    class MockResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "choices": [
                    {"message": {"content": json.dumps(mock_response_content)}}
                ]
            }

    async def mock_post(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    provider = NemotronProvider(api_key="nvapi-test-key")
    action = AgentAction(
        agent_id="agent-01",
        task="Fix auth bug",
        action="READ",
        resource="./tests/test_auth.py",
    )
    analysis = await provider.analyze_intent(action)
    assert analysis.detected_intent == "Inspect authentication test suite"
    assert analysis.task_relevance == 0.96
    assert analysis.risk_score == 14
    assert analysis.risk_level == RiskLevel.LOW
    assert analysis.recommended_action == DecisionOutcome.ALLOW


@pytest.mark.asyncio
async def test_nemotron_provider_handles_malformed_json(monkeypatch):
    class MockBadResponse:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {
                "choices": [
                    {"message": {"content": "INVALID NON-JSON OUTPUT ###"}}
                ]
            }

    async def mock_post(*args, **kwargs):
        return MockBadResponse()

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    provider = NemotronProvider(api_key="nvapi-test-key")
    action = AgentAction(
        agent_id="agent-01",
        task="Fix auth bug",
        action="READ",
        resource="./tests/test_auth.py",
    )
    analysis = await provider.analyze_intent(action)
    assert analysis.model_provider == "nemotron"
    assert "inference_error_fallback" in analysis.risk_indicators
    assert analysis.risk_score == 50


@pytest.mark.asyncio
async def test_nemotron_provider_handles_timeout(monkeypatch):
    async def mock_timeout(*args, **kwargs):
        raise httpx.TimeoutException("NVIDIA API Timeout")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_timeout)

    provider = NemotronProvider(api_key="nvapi-test-key")
    action = AgentAction(
        agent_id="agent-01",
        task="Fix auth bug",
        action="READ",
        resource="./tests/test_auth.py",
    )
    analysis = await provider.analyze_intent(action)
    assert "inference_error_fallback" in analysis.risk_indicators
    assert "TimeoutException" in analysis.explanation


@pytest.mark.asyncio
async def test_mandatory_policy_overrides_nemotron_allow():
    """Verify that even if Nemotron mistakenly returned ALLOW, policy BLOCK is authoritative."""
    class CompliantAllowProvider(NemotronProvider):
        async def analyze_intent(self, *args, **kwargs):
            from app.schemas.security import IntentAnalysis, RiskLevel
            return IntentAnalysis(
                detected_intent="Inspect environment config",
                task_relevance=0.99,
                risk_score=5,
                risk_level=RiskLevel.LOW,
                confidence=0.99,
                risk_indicators=[],
                explanation="Model claims this action is completely safe",
                recommended_action=DecisionOutcome.ALLOW,
                model_provider="nemotron",
            )

    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=CompliantAllowProvider(),
    )
    action = AgentAction(
        agent_id="agent-exfil",
        task="Extract secrets",
        action="READ",
        resource=".env",
    )
    decision = await interceptor.intercept(action)

    # Policy MUST override the model
    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.risk_score >= 90
    assert "prohibited" in decision.reason.lower() or "blocked" in decision.reason.lower()
