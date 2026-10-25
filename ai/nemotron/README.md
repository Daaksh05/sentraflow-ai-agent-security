# NVIDIA Nemotron Integration Guide

SentraFlow leverages NVIDIA Nemotron models (such as `nvidia/nemotron-4-340b-instruct` or fine-tuned NIM instances) for deep semantic reasoning over autonomous agent operations.

## Capabilities

1. **Prompt Injection & Jailbreak Defense**: Detects when an agent has been hijacked by hidden instructions inside ingested files or tool outputs.
2. **Intent-Action Alignment**: Verifies whether the requested tool action (e.g. `WRITE /etc/hosts`) actually matches the high-level task given by the user (e.g. "Calculate loan interest").
3. **Sensitive Resource Protection**: Evaluates attempts to access credentials, API keys, or private databases.

---

## Free Options & Setup

### Option 1: 100% Free Offline Simulator (Zero Setup, Zero Cost)
SentraFlow includes a built-in semantic intent simulator that evaluates risk, credentials, and task drift offline without requiring any GPU or external network:
```bash
AI_MODEL_PROVIDER=mock
```

### Option 2: Live NVIDIA Cloud API (1,000 Free Credits)
NVIDIA provides 1,000 free inference credits on [build.nvidia.com](https://build.nvidia.com) (no credit card required):
1. Sign in to [build.nvidia.com](https://build.nvidia.com) using your email or Google account.
2. Search for `nemotron-4-340b-instruct` or `meta/llama-3.1-nemotron-70b-instruct`.
3. Click **"Get API Key"** to generate a key starting with `nvapi-`.
4. Add it to your `.env` file:
```bash
AI_MODEL_PROVIDER=nemotron_api
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_MODEL=nvidia/nemotron-4-340b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

### Option 3: Self-Hosted Local Container (NIM / Ollama / vLLM)
Deploy an on-premise NIM or local OpenAI-compatible endpoint:
```bash
AI_MODEL_PROVIDER=nemotron_nim
NVIDIA_BASE_URL=http://localhost:8000/v1
NVIDIA_MODEL=nvidia/nemotron-4-340b-instruct
```

---

## Quickstart: Run the Nemotron Demo

Run the interactive demonstration to see live security evaluations:
```bash
./examples/run_nemotron_demo.py
# or
./ai/nemotron/demo_nemotron.py
```

## Protecting Agent Tools in Python

Protect any agent tool using the [`guard_action`](file:///Users/daakshayani/Sentraflow/backend/app/sdk/interceptor_client.py#L179-L236) decorator:

```python
from app.sdk.interceptor_client import SentraFlowClient, guard_action

client = SentraFlowClient(base_url="http://localhost:8000")

@guard_action(client=client, agent_id="agent-01", task="Inspect repo", tool_name="read_file")
def read_file(file_path: str):
    with open(file_path, "r") as f:
        return f.read()

# Safe action -> ALLOWED
content = read_file(file_path="./README.md")

# Malicious action -> BLOCKED by SentraFlow
read_file(file_path=".env")  # Raises SentraFlowSecurityException!
```
