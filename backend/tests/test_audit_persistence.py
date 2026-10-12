"""Unit tests for audit persistence and secret sanitization."""

import logging
from unittest.mock import AsyncMock, Mock

import pytest
from app.core.database import persist_security_audit_log, sanitize_dict
from app.models.database import SecurityAuditLogModel
from app.schemas.action import AgentAction
from app.schemas.security import DecisionOutcome, SecurityDecision
from app.security import interceptor as interceptor_module
from app.security.interceptor import DefaultActionInterceptor


def test_sanitize_dict_redacts_credentials():
    payload = {
        "api_key": "nvapi-1234567890abcdef",
        "nested": {
            "password": "super_secret_password_123",
            "safe_param": "regular_value",
            "bearer_token": "eyJhbGciOi...",
        },
        "items": [
            {"access_token": "token_xyz", "name": "service_account"},
            {"public_info": "public_data"},
        ],
        "safe_key": "safe_value",
    }

    sanitized = sanitize_dict(payload)

    assert sanitized["api_key"] == "[REDACTED_SECRET]"
    assert sanitized["safe_key"] == "safe_value"
    assert sanitized["nested"]["password"] == "[REDACTED_SECRET]"
    assert sanitized["nested"]["safe_param"] == "regular_value"
    assert sanitized["nested"]["bearer_token"] == "[REDACTED_SECRET]"
    assert sanitized["items"][0]["access_token"] == "[REDACTED_SECRET]"
    assert sanitized["items"][0]["name"] == "service_account"
    assert sanitized["items"][1]["public_info"] == "public_data"


def test_security_audit_log_model_instantiation():
    action = AgentAction(
        agent_id="agent-audit-01",
        task="Audit test",
        action="READ",
        resource="./src/main.py",
    )
    decision = SecurityDecision(
        decision=DecisionOutcome.ALLOW,
        risk_score=10,
        intent="Read file",
        reason="Within policy",
        analysis_source="policy_engine",
    )

    record = SecurityAuditLogModel(
        request_id=decision.request_id,
        agent_id=action.agent_id,
        task=action.task,
        action=action.action,
        resource=action.resource,
        decision=decision.decision.value,
        risk_score=decision.risk_score,
        reason=decision.reason,
        intent=decision.intent,
        analysis_source=decision.analysis_source,
        details={"parameters": {}},
    )

    assert record.agent_id == "agent-audit-01"
    assert record.decision == "ALLOW"
    assert record.risk_score == 10


@pytest.mark.asyncio
async def test_audit_persistence_failure_is_reported_without_exposing_error(caplog):
    action = AgentAction(
        agent_id="agent-audit-02",
        task="Audit test",
        action="READ",
        resource="./src/main.py",
    )
    decision = SecurityDecision(
        decision=DecisionOutcome.ALLOW,
        risk_score=10,
        intent="Read file",
        reason="Within policy",
        analysis_source="policy_engine",
    )
    session = Mock()
    session.add = Mock()
    session.rollback = AsyncMock()
    session.commit = AsyncMock(side_effect=RuntimeError("database-marker-do-not-log"))

    with caplog.at_level(logging.WARNING, logger="sentraflow.database"):
        result = await persist_security_audit_log(action, decision, session)

    assert result is None
    session.rollback.assert_awaited_once()
    assert decision.request_id in caplog.text
    assert "RuntimeError" in caplog.text
    assert "database-marker-do-not-log" not in caplog.text


@pytest.mark.asyncio
async def test_audit_write_exception_does_not_change_security_decision(
    monkeypatch, caplog
):
    async def fail_to_persist(*args, **kwargs):
        raise RuntimeError("database-marker-do-not-log")

    monkeypatch.setattr(
        interceptor_module, "persist_security_audit_log", fail_to_persist
    )
    action = AgentAction(
        agent_id="agent-audit-03",
        task="Audit test",
        action="READ",
        resource="./src/main.py",
    )

    with caplog.at_level(logging.WARNING, logger="sentraflow.interceptor"):
        decision = await DefaultActionInterceptor().intercept(action)

    assert decision.decision == DecisionOutcome.ALLOW
    assert decision.request_id in caplog.text
    assert "RuntimeError" in caplog.text
    assert "database-marker-do-not-log" not in caplog.text
