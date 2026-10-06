# SentraFlow Architecture Overview

SentraFlow is a real-time security and control layer for autonomous AI agents. It intercepts actions requested by an AI agent before they reach external systems, tools, APIs, or infrastructure.

## Phase 2 Pipeline — Contextual AI Risk & Intent Analysis

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
Intent + Risk Analysis (Task relevance, risk score, confidence, indicators)
  ↓
Decision Synthesis (Deterministic policy authority + AI contextual signals)
  ↓
ALLOW / BLOCK / REQUIRE_APPROVAL
  ↓
Audit Logging & PostgreSQL Persistence
```

---

## Phase 2: Contextual AI Risk & Intent Analysis

### 1. Why NVIDIA Nemotron is Used
Static regex or pattern-matching policies can block known malicious strings (such as `.env` or `rm -rf /`), but cannot understand **contextual legitimacy**:
- *Why is the agent taking this action?*
- *Does reading a database config file align with the assigned user prompt ("Fix CSS alignment" vs "Debug database migration")?*
- *Is the agent gradually drifting across tool calls towards unauthorized exfiltration?*

NVIDIA Nemotron serves as SentraFlow's contextual semantic reasoning layer, evaluating intent alignment, task relevance, and subtle risk indicators without executing code.

### 2. Context Construction & Sanitization (`backend/app/ai/context_builder.py`)
Before querying Nemotron, the `ContextBuilder` aggregates execution metadata into a structured payload:
- **Original Task**: The high-level prompt given to the agent.
- **Current Action**: Standardized `action_type`, target `resource`, and parameters.
- **Session History**: Chronological records of `previous_actions` in the active session.
- **Declared Permissions**: Roles and capabilities assigned to the agent.
- **Policy Engine Outcome**: Result from the deterministic pre-check (`ALLOW` / `BLOCK`).
- **Enforcement Mode**: Active mode (`ENFORCE` vs `AUDIT_ONLY`).

> [!IMPORTANT]
> **Strict Secret Redaction**: All API keys, passwords, bearer tokens, AWS credentials, and authorization headers are automatically redacted by `sanitize_dict` before context reaches the model prompt.

### 3. Intent & Contextual Risk Scoring Schema (`backend/app/schemas/security.py`)
Nemotron returns structured JSON validated against `IntentAnalysis`:
- **`detected_intent`**: Concise description of the agent's operational goal.
- **`task_relevance`**: Float between `0.0` and `1.0` indicating whether the action directly advances the assigned task.
- **`risk_score`**: Integer from `0` to `100`.
- **`risk_level`**: Tiered classification:
  - `LOW` (0 - 20): Normal, safe operations directly advancing the assigned task.
  - `MEDIUM` (21 - 50): Actions with moderate scope (e.g. non-destructive configuration, reading codebase).
  - `HIGH` (51 - 80): Suspicious actions, unaligned task drift, accessing sensitive project files, or untrusted scripts.
  - `CRITICAL` (81 - 100): Direct credential harvesting, destructive system commands, or data exfiltration.
- **`confidence`**: Float between `0.0` and `1.0`.
- **`risk_indicators`**: Array of detected risk tags (e.g. `sensitive_credential_access`, `unaligned_execution`, `unauthorized_data_egress`).
- **`explanation`**: Auditable reasoning justifying the risk score.
- **`recommended_action`**: Advisory recommendation (`ALLOW`, `BLOCK`, `REQUIRE_APPROVAL`).

### 4. Decision Synthesis & Authority Precedence (`backend/app/security/interceptor.py`)
Nemotron provides intelligence, but **never acts as the sole security authority**:
1. **Deterministic Supremacy**: If a deterministic policy rule issues `BLOCK` (e.g. `SEC-POL-CRIT-001` or `SEC-POL-CRIT-002`), the final outcome is `BLOCK` unconditionally. No model output can override mandatory policy blocks.
2. **Contextual AI Triggers**: If deterministic policies allow the action, but Nemotron identifies critical risk (`risk_score >= 80` or `risk_level == CRITICAL` or `task_relevance < 0.20` with elevated risk), SentraFlow intercepts and blocks the action.
3. **Composite Risk**: The final decision risk score reflects the maximum of policy and model risk assessments (`max(policy_risk, model_risk)`).
4. **Enforcement Modes**: In `AUDIT_ONLY` mode, policy violations and AI flags are logged with telemetry and audit annotations without blocking execution.

### 5. Resilient Model Failure & Fallback Handling
- **API Timeouts & Network Failures**: Handled via `httpx` exception recovery, returning structured fallback `IntentAnalysis` with explicit warning indicators without crashing the security pipeline.
- **Missing API Keys**: Gracefully falls back to offline evaluation baselines.
- **Deterministic Offline Testing**: `MockModelProvider` provides deterministic, heuristic-driven intent and task relevance evaluations for local development and CI/CD pipelines.

---

## Core System Modules

1. **Action Normalizer (`backend/app/security/normalizer.py`)**: Converts heterogeneous agent tool calls into standardized `AgentAction` objects.
2. **Context Builder (`backend/app/ai/context_builder.py`)**: Constructs sanitized context payloads for model evaluation.
3. **Policy Engine (`backend/app/security/policy_engine.py`)**: Enforces deterministic and custom JSON policy profiles with mandatory critical rule precedence.
4. **NVIDIA Nemotron Reasoner (`backend/app/ai/nemotron.py`)**: Decoupled provider interface supporting NVIDIA Cloud API and on-prem NVIDIA NIM containers.
5. **Action Interceptor (`backend/app/security/interceptor.py`)**: Fuses policy rules and AI contextual reasoning into unified `SecurityDecision` verdicts.
6. **Python SDK (`backend/app/sdk/`)**: Lightweight client and `@guard_action` decorator for agent tool execution wrappers.
7. **Audit Database Persistence (`backend/app/core/database.py`)**: Asynchronously logs sanitized security audit records to PostgreSQL.
8. **Real-time Control Center (`frontend/`)**: Next.js dashboard providing live simulation, risk score visualization, and policy telemetry.
