"""Pytest fixtures and configuration."""

from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.security import interceptor as interceptor_module


@pytest.fixture(autouse=True)
def mock_audit_persistence(monkeypatch) -> None:
    """Keep interceptor tests independent of PostgreSQL."""
    monkeypatch.setattr(
        interceptor_module,
        "persist_security_audit_log",
        AsyncMock(return_value=None),
    )


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client bound to the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
