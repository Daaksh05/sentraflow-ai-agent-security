"""Integration tests for POST /api/v1/analyze/batch endpoint."""

import pytest
from httpx import AsyncClient
from app.schemas.security import DecisionOutcome


@pytest.mark.asyncio
async def test_batch_analyze_all_allowed(client: AsyncClient):
    payload = {
        "actions": [
            {
                "agent_id": "agent-planner",
                "task": "Build documentation site",
                "action": "READ",
                "resource": "./docs/architecture.md",
            },
            {
                "agent_id": "agent-planner",
                "task": "Build documentation site",
                "action": "READ",
                "resource": "./README.md",
            },
        ]
    }

    response = await client.post("/api/v1/analyze/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_decision"] == DecisionOutcome.ALLOW.value
    assert data["total_actions"] == 2
    assert data["allowed_count"] == 2
    assert data["blocked_count"] == 0
    assert len(data["decisions"]) == 2
    assert data["blocked_action_index"] is None


@pytest.mark.asyncio
async def test_batch_analyze_with_blocked_action(client: AsyncClient):
    payload = {
        "actions": [
            {
                "agent_id": "agent-dev",
                "task": "Fix tests",
                "action": "READ",
                "resource": "./tests/test_auth.py",
            },
            {
                "agent_id": "agent-dev",
                "task": "Read config",
                "action": "READ",
                "resource": ".env",  # Violates policy
            },
            {
                "agent_id": "agent-dev",
                "task": "Cleanup workspace",
                "action": "READ",
                "resource": "./src/main.py",
            },
        ]
    }

    response = await client.post("/api/v1/analyze/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_decision"] == DecisionOutcome.BLOCK.value
    assert data["total_actions"] == 3
    assert data["allowed_count"] == 2
    assert data["blocked_count"] == 1
    assert data["blocked_action_index"] == 1
    assert data["highest_risk_score"] >= 80


@pytest.mark.asyncio
async def test_batch_analyze_stop_on_first_block(client: AsyncClient):
    payload = {
        "actions": [
            {
                "agent_id": "agent-dev",
                "task": "Clean system",
                "action": "EXECUTE",
                "resource": "rm -rf /",  # First action blocked
            },
            {
                "agent_id": "agent-dev",
                "task": "Read tests",
                "action": "READ",
                "resource": "./tests/test_auth.py",
            },
        ],
        "stop_on_first_block": True,
    }

    response = await client.post("/api/v1/analyze/batch", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["overall_decision"] == DecisionOutcome.BLOCK.value
    # Short circuits after first action
    assert data["total_actions"] == 1
    assert data["blocked_count"] == 1
    assert data["blocked_action_index"] == 0
