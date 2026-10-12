"""Tests for application startup and shutdown lifecycle."""

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.main as main


@pytest.mark.asyncio
async def test_lifespan_continues_when_database_initialization_fails(
    monkeypatch, caplog
):
    initialize_database = AsyncMock(return_value=False)
    dispose_engine = AsyncMock()
    monkeypatch.setattr(main, "init_db", initialize_database)
    monkeypatch.setattr(main, "engine", SimpleNamespace(dispose=dispose_engine))

    with caplog.at_level(logging.WARNING, logger="sentraflow"):
        async with main.lifespan(main.app):
            initialize_database.assert_awaited_once()
            dispose_engine.assert_not_awaited()

    dispose_engine.assert_awaited_once()
    assert "continuing without database persistence" in caplog.text
