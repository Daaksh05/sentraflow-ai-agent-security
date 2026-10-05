# SentraFlow Architecture Overview

SentraFlow is a real-time security and control layer for autonomous AI agents. It intercepts actions requested by an AI agent before they reach external systems, tools, APIs, or infrastructure.

## Phase 1 Interception Pipeline

```
Raw Agent Tool Call (LangChain / AutoGen / CrewAI / Custom)
                 ↓
      Action Normalizer (app.security.normalizer)
                 ↓
           AgentAction (Standardized action & resource)
                 ↓
      ActionContext (Permissions, History, Environment)
                 ↓
 SentraFlow Interceptor (app.security.interceptor)
                 ↓
 ┌───────────────────────────────┬───────────────────────────────┐
 │                               │                               │
 ▼                               ▼                               ▼
Deterministic Policy Engine    AI Intent Reasoner         Enforcement Mode
(Mandatory Critical Rules +    (NVIDIA Nemotron /          (ENFORCE vs
 Dynamic Policy Profiles)       NIM / Cloud API)            AUDIT_ONLY)
 └───────────────────────────────┴───────────────────────────────┘
                 ↓
         Decision Engine (ALLOW / BLOCK / REQUIRE_APPROVAL)
                 ↓
 ┌───────────────────────────────┬───────────────────────────────┐
 │                               │                               │
 ▼                               ▼                               ▼
SIEM Structured Audit Log       PostgreSQL Persistence        Verdict to Agent
(JSON with X-Request-ID)        (Sanitized Secret Redaction)  (Synchronous Gate)
```

## Core Modules & Capabilities

### 1. Action Normalizer (`backend/app/security/normalizer.py`)
Converts heterogeneous agent tool calls (`read_file`, `write_file`, `bash`, `python_repl`, `web_search`, `sql_query`) into standardized `AgentAction` objects mapped to standardized `ActionType` categories. Normalization strictly transforms the request representation and **never executes** actions within SentraFlow.

### 2. Action Context Layer (`backend/app/schemas/action.py`)
Injects rich contextual telemetry into action evaluations, including:
- Agent Identity & Session Correlation (`session_id`, `agent_id`)
- Declared Roles & Permissions (`permissions`)
- Action History (`previous_actions` in the active session)
- Sanitized Environment Variables & Host Metadata

### 3. Dynamic Policy Engine (`backend/app/security/policy_engine.py`)
Supports loading, validating, and switching JSON/YAML policy profiles at runtime (e.g. `policies/examples/default_strict.json` and `policies/examples/developer_sandbox.json`).
- **Mandatory Safety Precedence**: Critical safety rules (`SEC-POL-CRIT-001` protecting `.env`, `id_rsa`, `~/.aws/credentials`, and `SEC-POL-CRIT-002` blocking system destruction `rm -rf /`) are hardcoded at the top of the evaluation chain and cannot be bypassed or overridden by custom policy profiles.

### 4. Batch Action Interception (`POST /api/v1/analyze/batch`)
Allows agent orchestration runtimes to submit multi-step plans or execution graphs for pre-flight security evaluation. Calculates aggregate risk metrics, identifies the earliest blocking action, and supports fail-fast short-circuiting (`stop_on_first_block`).

### 5. Configurable Enforcement Modes (`ENFORCE` vs `AUDIT_ONLY`)
- **ENFORCE Mode**: Security policy violations and critical AI risk scores immediately block tool execution (`decision = BLOCK`).
- **AUDIT_ONLY Mode**: Violations are flagged and logged with telemetry annotations while permitting execution (`decision = ALLOW`, `reason = [AUDIT_ONLY MODE] Violation flagged...`), ensuring fail-secure telemetry without zeroing out risk scores.

### 6. Python SDK & Interceptor Decorator (`backend/app/sdk/`)
Lightweight integration library for AI agents:
- `SentraFlowClient`: Synchronous and asynchronous clients for single and batch action analysis.
- `@guard_action`: Function decorator intercepting agent tool invocations before execution and raising `SentraFlowSecurityException` upon `BLOCK` verdicts.

### 7. Database Audit Persistence (`backend/app/core/database.py`)
Persists all evaluations to PostgreSQL `security_audit_logs` table via async SQLAlchemy.
- **Strict Secret Redaction**: All API keys, passwords, tokens, bearer headers, and credentials are automatically redacted before persistence.

### 8. NVIDIA Nemotron AI Reasoning (`backend/app/ai/`)
Decoupled model provider abstraction (`ModelProvider`, `NemotronProvider`, `MockModelProvider`) providing semantic intent analysis and risk scoring via NVIDIA Cloud API or self-hosted NVIDIA NIM containers.
