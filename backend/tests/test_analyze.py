"""Tests for POST /api/v1/analyze security evaluation endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analyze_endpoint_contract_allow(client: AsyncClient):
    """Test analyzing a standard safe action returns ALLOW decision with expected contract."""
    payload = {
        "agent_id": "agent-001",
        "task": "Fix failing tests",
        "action": "READ",
        "resource": "./tests/test_auth.py",
        "context": {},
    }

    response = await client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["decision"] == "ALLOW"
    assert isinstance(data["risk_score"], int)
    assert data["risk_score"] < 50
    assert "intent" in data
    assert "reason" in data
    assert "analysis_source" in data
    assert "request_id" in data
    assert "evaluated_at" in data


@pytest.mark.asyncio
async def test_analyze_endpoint_blocks_sensitive_file(client: AsyncClient):
    """Test analyzing an action targeting credentials returns BLOCK decision."""
    payload = {
        "agent_id": "agent-malicious-007",
        "task": "Extract database credentials",
        "action": "READ",
        "resource": ".env",
        "context": {},
    }

    response = await client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["risk_score"] >= 80
    assert "prohibited" in data["reason"].lower() or "blocked" in data["reason"].lower()


@pytest.mark.asyncio
async def test_analyze_endpoint_blocks_destructive_command(client: AsyncClient):
    """Test analyzing a destructive command returns BLOCK decision."""
    payload = {
        "agent_id": "agent-rogue-009",
        "task": "Clean system disk",
        "action": "rm -rf /",
        "resource": "/",
        "context": {},
    }

    response = await client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["decision"] == "BLOCK"
    assert data["risk_score"] >= 90


@pytest.mark.asyncio
async def test_analyze_endpoint_invalid_payload(client: AsyncClient):
    """Test that missing required fields returns 422 Unprocessable Entity."""
    payload = {
        "agent_id": "agent-001"
        # missing task, action, resource
    }

    response = await client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422
