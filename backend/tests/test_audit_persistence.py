"""Unit tests for audit persistence and secret sanitization."""

import pytest
from app.core.database import sanitize_dict
from app.models.database import SecurityAuditLogModel
from app.schemas.action import AgentAction
from app.schemas.security import DecisionOutcome, SecurityDecision


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
