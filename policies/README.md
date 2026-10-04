# SentreFlow Security Policies

SentreFlow enforces deterministic security policies alongside AI intent analysis.
Policies establish non-negotiable boundaries that block unsafe operations regardless of LLM reasoning.

## Policy Hierarchy

1. **Deterministic Rule Boundary**: Absolute blocks (e.g., accessing `.env`, `.ssh/`, executing `rm -rf /`).
2. **Context & Intent Analyzer (Nemotron)**: Evaluates semantic alignment and covert risks.
3. **Composite Security Decision**: Fuses rule checks and AI evaluation into a final `ALLOW` or `BLOCK` decision.

## Example Policies

- `policies/examples/default_strict.json`: Standard production lockdown policy.
- `policies/examples/developer_sandbox.json`: Permissive sandbox policy for development testing.
