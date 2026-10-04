# SentreFlow Security Model & Trust Boundary

## Core Principles

1. **Pre-Execution Gate**: No autonomous action executes without passing through the SentreFlow policy boundary.
2. **Deterministic Supremacy**: Static policy rules override AI model output. If a policy specifies `BLOCK` for accessing `.env`, no amount of model reasoning can allow it.
3. **AI as an Input, Not Final Authority**: Model reasoning from NVIDIA Nemotron provides semantic context and detects novel attacks, but the final boundary remains deterministic.
4. **Separation of Analysis and Execution**: SentreFlow evaluates and advises on actions, maintaining a strict boundary from execution engines.
5. **Full Traceability**: Every evaluation produces a structured audit record with a unique `request_id`, agent identifier, action verb, target resource, and detailed rationale.
