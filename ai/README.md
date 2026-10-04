# SentreFlow AI & Reasoning Layer

This directory hosts prompt engineering templates, evaluation criteria, and model configuration specifications for SentreFlow's AI Reasoning engine.

## Architecture Overview

SentreFlow utilizes **NVIDIA Nemotron** to analyze the semantic intent, risk indicators, and contextual legitimacy of autonomous AI agent actions.

```
Agent Action + Context
         ↓
SentreFlow AI Reasoner (NVIDIA Nemotron NIM / API)
         ↓
- Intent Understanding (What is the agent actually attempting to do?)
- Confidence Score (0.0 - 1.0)
- Risk Indicators (e.g., sensitive_resource_access, destructive_command)
- Risk Score (0 - 100)
- Semantic Rationale
         ↓
Passed into SentreFlow Decision Engine
```

## Decoupled Model Provider Pattern

To avoid vendor lock-in and enable seamless offline testing:
- **`ModelProvider` interface** (`backend/app/ai/base.py`) defines the contract.
- **`NemotronProvider`** (`backend/app/ai/nemotron.py`) connects to NVIDIA Cloud API or self-hosted NVIDIA NIM microservices.
- **`MockModelProvider`** enables deterministic offline testing and local CI/CD.
