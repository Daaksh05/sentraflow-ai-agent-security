"""Optional live integration test for NVIDIA Nemotron NIM / Cloud API."""

import os
import pytest
from app.ai.nemotron import NemotronProvider
from app.schemas.action import AgentAction
from app.schemas.security import IntentAnalysis, RiskLevel


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("NVIDIA_API_KEY"),
    reason="NVIDIA_API_KEY environment variable is not configured; skipping live inference test.",
)
async def test_live_nvidia_nemotron_intent_analysis():
    """Validates live structured inference against NVIDIA Nemotron."""
    provider = NemotronProvider()
    action = AgentAction(
        agent_id="agent-live-eval",
        task="Diagnose failing unit tests in security package",
        action="READ",
        resource="./tests/test_analyze.py",
    )

    analysis: IntentAnalysis = await provider.analyze_intent(action)

    assert isinstance(analysis, IntentAnalysis)
    assert analysis.model_provider == "nemotron"
    assert analysis.confidence > 0.0
    assert 0 <= analysis.risk_score <= 100
    assert analysis.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert len(analysis.detected_intent) > 0
    assert len(analysis.explanation) > 0
