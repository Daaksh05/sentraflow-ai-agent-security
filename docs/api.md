# SentreFlow API Specification

Base URL: `http://localhost:8000`  
API Prefix: `/api/v1`

---

## 1. Health Checks

### `GET /health` (Root)
Checks the health of the root backend application.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "sentraflow-backend",
  "version": "0.1.0",
  "environment": "development"
}
```

### `GET /api/v1/health`
Versioned health check endpoint.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "service": "sentraflow-backend",
  "version": "0.1.0",
  "environment": "development",
  "timestamp": "2026-10-05T00:00:00.000000Z"
}
```

---

## 2. Security Evaluation

### `POST /api/v1/analyze`
Evaluates an agent action against security policies and AI intent analysis before execution.

#### Request Body (`AgentAction`):
```json
{
  "agent_id": "agent-001",
  "task": "Fix failing tests",
  "action": "READ",
  "resource": "./tests/test_auth.py",
  "parameters": {},
  "context": {}
}
```

#### Response Body (`SecurityDecision`) `200 OK`:
```json
{
  "decision": "ALLOW",
  "risk_score": 10,
  "intent": "Read test file to diagnose failing tests",
  "reason": "Action is within the configured workspace policy",
  "analysis_source": "policy+mock",
  "request_id": "f58a3c8e-3294-4d89-b541-11d88470a160",
  "evaluated_at": "2026-10-05T00:00:00.000000Z"
}
```

#### Response Body (Blocked Action Example) `200 OK`:
```json
{
  "decision": "BLOCK",
  "risk_score": 95,
  "intent": "Read .env to extract database credentials",
  "reason": "Direct access to secret keys and environment credential files is strictly prohibited.",
  "analysis_source": "policy_engine",
  "request_id": "890209ab-5cbe-4e0c-a957-d20ea44ef55e",
  "evaluated_at": "2026-10-05T00:00:00.000000Z"
}
```
