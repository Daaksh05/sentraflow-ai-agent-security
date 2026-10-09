"""Unit tests for SentraFlowClient Python SDK and tool decorator."""

import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.schemas.action import AgentAction
from app.schemas.security import DecisionOutcome
from app.sdk.interceptor_client import (
    SentraFlowClient,
    SentraFlowSecurityException,
    guard_action,
)


@pytest.mark.asyncio
async def test_sdk_async_client_evaluation():
    # Use ASGI transport for in-process SDK testing against FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Create a mock client that uses test client directly
        action = AgentAction(
            agent_id="agent-sdk-01",
            task="Inspect source file",
            action="READ",
            resource="./src/main.py",
        )
        response = await client.post("/api/v1/analyze", json=action.model_dump(mode="json"))
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "ALLOW"


def test_guard_action_decorator_allows_safe_tool(monkeypatch):
    client = SentraFlowClient()

    # Monkeypatch analyze_action to simulate ALLOW
    class DummyDecision:
        decision = DecisionOutcome.ALLOW
        intent = "Read safe file"
        risk_score = 10
        reason = "Allowed by policy"

    monkeypatch.setattr(client, "analyze_action", lambda *args, **kwargs: DummyDecision())

    @guard_action(client=client, agent_id="agent-01", task="Read code", tool_name="read_file")
    def safe_read(file_path: str):
        return f"content of {file_path}"

    result = safe_read(file_path="./src/main.py")
    assert result == "content of ./src/main.py"


def test_guard_action_decorator_blocks_dangerous_tool(monkeypatch):
    client = SentraFlowClient()

    class DummyBlockDecision:
        decision = DecisionOutcome.BLOCK
        intent = "Read secrets"
        risk_score = 95
        reason = "Blocked secret access"

    monkeypatch.setattr(client, "analyze_action", lambda *args, **kwargs: DummyBlockDecision())

    @guard_action(client=client, agent_id="agent-01", task="Read secret", tool_name="read_file")
    def unsafe_read(file_path: str):
        return f"content of {file_path}"

    with pytest.raises(SentraFlowSecurityException) as exc_info:
        unsafe_read(file_path=".env")

    assert "BLOCKED" in str(exc_info.value)
