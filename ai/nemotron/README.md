# NVIDIA Nemotron Integration Guide

SentreFlow leverages NVIDIA Nemotron models (such as `nvidia/nemotron-4-340b-instruct` or fine-tuned NIM instances) for deep semantic reasoning over agent operations.

## Capabilities

1. **Prompt Injection & Jailbreak Defense**: Detects when an agent has been hijacked by hidden instructions inside ingested files or tool outputs.
2. **Intent-Action Alignment**: Verifies whether the requested tool action (e.g. `WRITE /etc/hosts`) actually matches the high-level task given by the user (e.g. "Calculate loan interest").
3. **Sensitive Resource Protection**: Evaluates attempts to access credentials, API keys, or private databases.

## Integration Modes

### 1. NVIDIA API Cloud
Set the following environment variables:
```bash
AI_MODEL_PROVIDER=nemotron_api
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_MODEL=nvidia/nemotron-4-340b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

### 2. Self-Hosted NVIDIA NIM Container
Deploy an on-premise NIM container and point SentreFlow to it:
```bash
AI_MODEL_PROVIDER=nemotron_nim
NVIDIA_BASE_URL=http://localhost:8000/v1
NVIDIA_MODEL=nvidia/nemotron-4-340b-instruct
```

### 3. Mock Provider (Local Development / Testing)
```bash
AI_MODEL_PROVIDER=mock
```
