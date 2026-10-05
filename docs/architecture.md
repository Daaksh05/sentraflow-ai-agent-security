# SentraFlow Architecture Overview

SentraFlow is a real-time security and control layer for autonomous AI agents. It intercepts actions requested by an AI agent before they reach external systems, tools, APIs, or infrastructure.

## System Topology

```
+-------------------------------------------------------------+
|                      User Prompt / Task                     |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
|                     Autonomous AI Agent                     |
|           (LangChain / AutoGen / CrewAI / Custom)           |
+-------------------------------------------------------------+
                              |
                              | Intercepted Action Request
                              v
+=============================================================+
|                      SentraFlow Engine                      |
|                                                             |
|   +---------------------+        +----------------------+   |
|   |    Policy Engine    |        | Intent & Context     |   |
|   |  (Deterministic)    |        | Analyzer (Nemotron)  |   |
|   +---------------------+        +----------------------+   |
|              \                              /               |
|               \                            /                |
|                v                          v                 |
|             +--------------------------------+              |
|             |        Decision Engine         |              |
|             |        (ALLOW / BLOCK)         |              |
|             +--------------------------------+              |
|                             |                               |
|                             v                               |
|             +--------------------------------+              |
|             |     Structured Audit Logger    |              |
|             +--------------------------------+              |
+=============================================================+
                              |
                     [ALLOW]  |  [BLOCK]
             +----------------+----------------+
             |                                 |
             v                                 v
+------------------------+         +--------------------------+
|  External Tool / API   |         | Execution Aborted        |
|  Execution Succeeds    |         | with Security Reason     |
+------------------------+         +--------------------------+
```

## Core Modules

### 1. Interceptor Layer (`backend/app/security/interceptor.py`)
Provides the interception hook (`ActionInterceptor`) that captures all requested actions and routes them through the evaluation pipeline.

### 2. Policy Engine (`backend/app/security/policy_engine.py`)
Enforces static and dynamic rule sets deterministically to guarantee absolute control boundaries.

### 3. Model Provider Abstraction (`backend/app/ai/base.py`)
Decouples LLM inference from security business logic. Supports NVIDIA Nemotron (NIM / Cloud API) and offline mocks.

### 4. Decision Engine (`backend/app/schemas/security.py`)
Fuses policy rule matching and AI semantic risk scoring into an auditable `SecurityDecision`.

### 5. Control Center Dashboard (`frontend/`)
Next.js + TypeScript dashboard for real-time observability, policy configuration, and action simulation.
