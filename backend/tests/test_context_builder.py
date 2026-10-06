"""Unit tests for ContextBuilder and secret sanitization for AI reasoning."""

import pytest
from app.ai.context_builder import ContextBuilder
from app.schemas.action import ActionContext, AgentAction, PreviousAction
from app.schemas.security import DecisionOutcome, PolicyDecision


def test_context_builder_structures_all_fields():
    action = AgentAction(
        agent_id="agent-coder-01",
        task="Fix authentication bug",
        action="READ",
        resource="./tests/test_auth.py",
        parameters={"line_number": 42},
        context={"editor": "vscode"},
    )
    context = ActionContext(
        session_id="sess-12345",
        permissions=["repo:read", "test:run"],
        previous_actions=[
            PreviousAction(action="READ", resource="pytest.ini", decision="ALLOW")
        ],
        environment_variables={"ENV": "dev"},
    )
    policy_decision = PolicyDecision(
        decision=DecisionOutcome.ALLOW,
        reason="Within workspace policy",
        risk_score=10,
        policy_id="SEC-POL-003",
        policy_name="Allow Workspace Read",
    )

    payload = ContextBuilder.build_context(
        action=action,
        context=context,
        policy_decision=policy_decision,
        enforcement_mode="ENFORCE",
    )

    assert payload["agent_id"] == "agent-coder-01"
    assert payload["session_id"] == "sess-12345"
    assert payload["original_task"] == "Fix authentication bug"
    assert payload["current_action"]["action"] == "READ"
    assert payload["current_action"]["resource"] == "./tests/test_auth.py"
    assert payload["declared_permissions"] == ["repo:read", "test:run"]
    assert len(payload["previous_actions"]) == 1
    assert payload["previous_actions"][0]["resource"] == "pytest.ini"
    assert payload["policy_result"]["outcome"] == "ALLOW"
    assert payload["enforcement_mode"] == "ENFORCE"


def test_context_builder_sanitizes_credentials_from_payload():
    action = AgentAction(
        agent_id="agent-unsafe",
        task="Authenticate with third party API",
        action="AUTH",
        resource="https://api.external.com/oauth/token",
        parameters={
            "client_secret": "super_secret_client_secret_999",
            "api_key": "nvapi-live-secret-key",
            "safe_header": "application/json",
        },
        context={
            "authorization": "Bearer eyJhbGciOi...",
            "session_token": "token_abc123",
        },
    )
    context = ActionContext(
        environment_variables={
            "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "DATABASE_PASSWORD": "db_password_root",
            "STAGE": "production",
        }
    )

    payload = ContextBuilder.build_context(action=action, context=context)

    # Verify all secrets are redacted
    params = payload["current_action"]["parameters"]
    assert params["client_secret"] == "[REDACTED_SECRET]"
    assert params["api_key"] == "[REDACTED_SECRET]"
    assert params["safe_header"] == "application/json"

    meta = payload["current_action"]["metadata"]
    assert meta["authorization"] == "[REDACTED_SECRET]"
    assert meta["session_token"] == "[REDACTED_SECRET]"

    env = payload["environment_context"]
    assert env["AWS_SECRET_ACCESS_KEY"] == "[REDACTED_SECRET]"
    assert env["DATABASE_PASSWORD"] == "[REDACTED_SECRET]"
    assert env["STAGE"] == "production"
