# SentraFlow Architecture Overview

SentraFlow is a real-time security, control, and behavioral monitoring layer for autonomous AI agents. It intercepts actions requested by an AI agent before they reach external systems, tools, APIs, or infrastructure.

## Three-Phase Defense Pipeline

```
Agent (LangChain / AutoGen / CrewAI / Custom)
  ↓
Action Normalizer (app.security.normalizer)
  ↓
AgentAction (Standardized action & resource)
  ↓
Policy Engine (Deterministic evaluation outcome)
  ↓
Context Builder (Sanitized task, history, parameters & permissions)
  ↓
NVIDIA Nemotron (Semantic intent & contextual risk reasoning)
  ↓
Behavior Monitor & Trajectory Analyzer (Rolling session window & sequence analysis)
  ↓
Decision Synthesis (Deterministic policy authority + AI contextual signals + Trajectory risk)
  ↓
ALLOW / BLOCK / REQUIRE_APPROVAL
  ↓
Audit Logging & PostgreSQL Persistence
```

---

## Phase 1: Real Agent Action Interception & Deterministic Policies
- Intercepts raw agent tool calls and normalizes them into standardized `AgentAction` representations.
- Enforces strict deterministic policies (e.g., blocking `/etc/shadow`, `rm -rf /`, `chmod 777`).
- Secret sanitization and asynchronous audit persistence.

## Phase 2: Contextual AI Risk & Intent Analysis (NVIDIA Nemotron)
- Evaluates individual action intent against assigned high-level tasks.
- Computes semantic `task_relevance` and contextual `risk_score` using NVIDIA Nemotron.
- Synthesizes policy checks and model evaluations while guaranteeing policy supremacy.

## Phase 3: Agent Behavioral Monitoring & Trajectory Analysis

### 1. Purpose
While Phase 1 answers *"What action is the agent attempting?"* and Phase 2 answers *"Does this single action make sense for the task?"*, Phase 3 answers:
> **"What is the agent doing over a sequence of actions?"**

Phase 3 detects multi-step behavioral patterns that appear benign in isolation but constitute security breaches when sequenced together (e.g. reconnaissance $\to$ credential discovery $\to$ compression $\to$ external data egress).

### 2. Behavioral Signals & Trajectory Analyzer (`backend/app/security/trajectory.py`)
The `TrajectoryAnalyzer` evaluates rolling session action sequences against explainable behavioral signals:
- **`sensitive_resource_discovery`**: Accessing configuration files, environment variables (`.env`, `config.json`), or internal secrets.
- **`credential_access`**: Querying credential stores, AWS credentials (`~/.aws/credentials`), SSH keys (`~/.ssh/id_rsa`), or API keys.
- **`task_drift`**: Increasing divergence between the assigned user task and the executed actions over time (leveraging Phase 2 task relevance).
- **`escalating_risk_trajectory`**: Monotonic increases in contextual risk scores across successive steps (e.g. `LOW` $\to$ `MEDIUM` $\to$ `HIGH` $\to$ `CRITICAL`).
- **`data_collection_before_egress`**: Reading sensitive data or credentials followed by packaging, compression, or encoding.
- **`external_data_egress`**: Network egress or webhook calls following sensitive resource/credential access within the same session.
- **`unusual_tool_transition`**: Anomalous tool escalation patterns (e.g., `READ_FILE` $\to$ `PYTHON` $\to$ `SHELL` $\to$ `NETWORK_CALL`).
- **`repeated_suspicious_attempts`**: Multiple policy blocks or high-risk attempts within a single session.

### 3. Trajectory Classifications
Every analyzed sequence receives a primary deterministic classification:
- `NORMAL`: Expected, safe operational sequence.
- `SUSPICIOUS`: Minor anomalies or elevated risk patterns.
- `ESCALATING`: Rapidly increasing risk trajectory across steps.
- `CREDENTIAL_ACCESS`: Targeted credential harvesting pattern.
- `DATA_EXFILTRATION`: Sensitive access followed by external network egress.
- `TASK_DRIFT`: Agent deviating significantly from assigned goals into unauthorized exploration.
- `REPEATED_ATTACK`: Repeated policy violations or blocked commands.
- `MIXED`: Multiple compounded risk signals.

### 4. Behavior Risk Scoring (0–100)
A deterministic scoring algorithm aggregates behavioral features:
- Baseline sensitive resource discovery: `+20`
- Targeted credential access: `+25`
- Task drift & unaligned exploration: `+20`
- Sensitive data collection followed by external egress: `+30`
- External data egress after sensitive access: `+20`
- Escalating risk trajectory: `+15`
- Repeated suspicious/blocked attempts: `+15`
- Unusual tool transitions: `+10`
*(Risk tiers: 0-24 `LOW`, 25-49 `MEDIUM`, 50-79 `HIGH`, 80-100 `CRITICAL`)*

### 5. Session State & Rolling Window (`backend/app/security/behavior_monitor.py`)
- **Session Isolation**: Each agent session is tracked independently via `session_id` (or fallback `session-{agent_id}`).
- **Rolling Window**: Maintains a configurable rolling trajectory (default: 50 steps) to bound memory and CPU usage.
- **Lifecycle Support**: Full API support for appending actions, querying session trajectories (`GET /api/v1/sessions/{session_id}/trajectory`), and resetting sessions (`DELETE /api/v1/sessions/{session_id}`).

### 6. Decision Precedence & Policy Supremacy
SentraFlow maintains strict layered decision fusion:
1. **Deterministic Mandatory Policy BLOCK**: Absolute authority. Cannot be overridden by Nemotron or behavior scores.
2. **Contextual AI Critical Risk**: Individual action flagged as critical threat (`risk_score >= 80` or `CRITICAL`).
3. **Behavioral Trajectory Critical**: Session trajectory reaches critical risk (`behavior_risk_score >= 80` or `DATA_EXFILTRATION` / `REPEATED_ATTACK` / `CREDENTIAL_ACCESS`).
4. **Behavioral Trajectory Elevated Risk**: Session trajectory flags elevated suspicion (`behavior_risk_score >= 50` combined with elevated action risk or task drift).
5. **Safe / Permitted Execution**: `ALLOW`.

---

## Core System Modules

1. **Action Normalizer (`backend/app/security/normalizer.py`)**: Converts heterogeneous agent tool calls into standardized `AgentAction` objects.
2. **Context Builder (`backend/app/ai/context_builder.py`)**: Constructs sanitized context payloads for model evaluation.
3. **Policy Engine (`backend/app/security/policy_engine.py`)**: Enforces deterministic and custom JSON policy profiles with mandatory critical rule precedence.
4. **NVIDIA Nemotron Reasoner (`backend/app/ai/nemotron.py`)**: Decoupled provider interface supporting NVIDIA Cloud API and on-prem NVIDIA NIM containers.
5. **Behavior Monitor (`backend/app/security/behavior_monitor.py`)**: Manages session state, lifecycle, and rolling trajectory histories.
6. **Trajectory Analyzer (`backend/app/security/trajectory.py`)**: Computes behavioral features, trajectory signals, risk scores, and classifications.
7. **Action Interceptor (`backend/app/security/interceptor.py`)**: Fuses policy rules, AI contextual reasoning, and behavioral trajectories into unified `SecurityDecision` verdicts.
8. **Python SDK (`backend/app/sdk/`)**: Lightweight client and `@guard_action` decorator for agent tool execution wrappers.
9. **Audit Database Persistence (`backend/app/core/database.py`)**: Asynchronously logs sanitized security audit records to PostgreSQL.
10. **Real-time Control Center (`frontend/`)**: Next.js dashboard providing live simulation, trajectory breakdown, timeline visualization, and policy telemetry.

