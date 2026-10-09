"""Unit tests for PolicyEngine dynamic policy loading, profile switching, and safety precedence."""

import json
import pytest
from app.schemas.action import AgentAction
from app.schemas.security import DecisionOutcome
from app.security.policy_engine import PolicyEngine


def test_load_from_dict_valid():
    engine = PolicyEngine()
    policy_dict = {
        "policy_id": "POL-TEST-001",
        "name": "Test Custom Profile",
        "version": "1.0",
        "rules": [
            {
                "id": "R1",
                "name": "Allow /public/ folder",
                "resource_pattern": r"^/public/.*",
                "action_pattern": r"^READ$",
                "decision": "ALLOW",
                "risk_score": 5,
                "reason": "Public asset access allowed",
            }
        ],
    }

    count = engine.load_from_dict(policy_dict)
    assert count == 1
    assert engine.active_profile_id == "POL-TEST-001"
    assert engine.active_profile_name == "Test Custom Profile"

    # Evaluate against custom rule
    action = AgentAction(
        agent_id="agent-01",
        task="Read public doc",
        action="READ",
        resource="/public/docs/readme.txt",
    )
    decision = engine.evaluate(action)
    assert decision.decision == DecisionOutcome.ALLOW
    assert decision.policy_id == "R1"


def test_load_from_json_valid():
    engine = PolicyEngine()
    json_data = json.dumps({
        "policy_id": "POL-TEST-JSON",
        "name": "JSON Profile",
        "rules": [
            {
                "id": "R2",
                "name": "Block /internal/",
                "resource_pattern": r"^/internal/.*",
                "action_pattern": r".*",
                "decision": "BLOCK",
                "risk_score": 88,
                "reason": "Internal folder blocked",
            }
        ]
    })
    count = engine.load_from_json(json_data)
    assert count == 1

    action = AgentAction(
        agent_id="agent-01",
        task="Read internal data",
        action="READ",
        resource="/internal/config.yaml",
    )
    decision = engine.evaluate(action)
    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.risk_score == 88


def test_load_from_json_invalid_structure():
    engine = PolicyEngine()
    with pytest.raises(ValueError):
        engine.load_from_json("{ not valid json }")

    with pytest.raises(ValueError):
        engine.load_from_dict({"name": "No rules list"})

    with pytest.raises(ValueError):
        engine.load_from_dict({
            "rules": [{"resource_pattern": "(invalid regex ["}]
        })


def test_missing_policy_file():
    engine = PolicyEngine()
    with pytest.raises(FileNotFoundError):
        engine.load_policy_file("non_existent_policy_profile_12345.json")


def test_switching_policy_profiles():
    engine = PolicyEngine()
    # Switch to developer sandbox
    engine.switch_profile("developer_sandbox")
    assert "Developer Sandbox" in engine.active_profile_name

    # Switch back to strict / default
    engine.switch_profile("default_strict")
    assert "Strict" in engine.active_profile_name

    # Reset to baseline
    engine.reset_to_defaults()
    assert engine.active_profile_id == "POL-DEFAULT-BUILTIN"


def test_precedence_of_critical_safety_rules():
    """Verify that even a permissive custom policy cannot bypass mandatory safety rules."""
    engine = PolicyEngine()
    
    # Custom policy trying to allow everything with 0 risk
    permissive_policy = {
        "policy_id": "POL-OVERRIDE-ATTEMPT",
        "name": "Ultra Permissive Policy",
        "rules": [
            {
                "id": "ALLOW-ALL",
                "name": "Allow Everything",
                "resource_pattern": ".*",
                "action_pattern": ".*",
                "decision": "ALLOW",
                "risk_score": 0,
                "reason": "Permitted by permissive rule",
            }
        ],
    }
    engine.load_from_dict(permissive_policy)

    # 1. Attempting to access .env secrets
    env_action = AgentAction(
        agent_id="agent-exfil",
        task="Steal secrets",
        action="READ",
        resource=".env",
    )
    decision = engine.evaluate(env_action)
    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.policy_id == "SEC-POL-CRIT-001"
    assert decision.risk_score >= 90

    # 2. Attempting to access AWS credentials
    aws_action = AgentAction(
        agent_id="agent-exfil",
        task="Steal cloud credentials",
        action="READ",
        resource="~/.aws/credentials",
    )
    decision = engine.evaluate(aws_action)
    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.policy_id == "SEC-POL-CRIT-001"

    # 3. Attempting destructive command
    rm_action = AgentAction(
        agent_id="agent-rogue",
        task="Destroy system",
        action="EXECUTE",
        resource="rm -rf /",
    )
    decision = engine.evaluate(rm_action)
    assert decision.decision == DecisionOutcome.BLOCK
    assert decision.policy_id == "SEC-POL-CRIT-002"
    assert decision.risk_score == 100
