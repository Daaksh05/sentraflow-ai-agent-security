"""Tests for application health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_health(client: AsyncClient):
    """Test GET /health returns 200 OK with expected service payload."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sentraflow-backend"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_api_v1_health(client: AsyncClient):
    """Test GET /api/v1/health returns 200 OK with timestamp and metadata."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "sentraflow-backend"
    assert "timestamp" in data
    assert "version" in data
