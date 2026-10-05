# SentraFlow — AI Agent Security & Control Platform

> **Real-time security layer sitting between autonomous AI agents and external tools, APIs, and execution systems.**

SentraFlow monitors actions requested by autonomous AI agents, evaluates intent and security risk using deterministic policies and **NVIDIA Nemotron** reasoning, and issues an **ALLOW** or **BLOCK** verdict with auditable justification.

---

## High-Level Architecture

```
User gives task
      ↓
Autonomous AI Agent
      ↓
Agent decides to perform an action
      ↓
SentraFlow Security Layer
      ├── Policy Engine (Deterministic Rules)
      ├── Intent & Context Analyzer (NVIDIA Nemotron)
      ├── Behavior Monitor
      └── Decision Engine
      ↓
ALLOW / BLOCK Verdict
      ↓
External Tool / API / System
      ↓
Result + Structured Audit Feedback
```

---

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic v2, Uvicorn, SQLAlchemy, PostgreSQL, Redis
- **AI Reasoning**: NVIDIA Nemotron (`nvidia/nemotron-4-340b-instruct` / NVIDIA NIM) with abstract `ModelProvider` layer
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Lucide Icons
- **Infrastructure**: Docker, Docker Compose

---

## Repository Structure

```
sentraflow/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (v1 health, security analyze)
│   │   ├── core/         # Settings and structured security logging
│   │   ├── models/       # SQLAlchemy database models
│   │   ├── schemas/      # Pydantic schemas (AgentAction, SecurityDecision)
│   │   ├── services/     # Security service orchestration
│   │   ├── security/     # PolicyEngine, PolicyRule, ActionInterceptor
│   │   ├── ai/           # ModelProvider, NemotronProvider, MockModelProvider
│   │   └── main.py       # FastAPI application entrypoint
│   ├── tests/            # Pytest test suite (12 passed)
│   ├── requirements.txt
│   ├── pytest.ini
│   └── Dockerfile
│
├── frontend/
│   ├── app/              # Next.js App Router (layout, dashboard page, styles)
│   ├── components/       # UI components, navbar, simulation tester, stat cards
│   ├── lib/              # API client and style helpers
│   ├── types/            # TypeScript interfaces matching backend models
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── Dockerfile
│
├── ai/
│   ├── nemotron/         # NVIDIA Nemotron NIM/API setup guides
│   ├── prompts/          # Semantic intent analysis prompt templates
│   └── README.md
│
├── policies/
│   ├── examples/         # Sample JSON policies (strict prod, dev sandbox)
│   └── README.md
│
├── docs/
│   ├── architecture.md   # Architectural overview and topology
│   ├── api.md            # API contract documentation
│   └── security-model.md # Security boundary and trust principles
│
├── docker-compose.yml    # Compose file for backend, frontend, postgres, redis
├── .env.example          # Environment variables template (no secrets committed)
├── .gitignore
├── README.md
└── LICENSE               # MIT License
```

---

## Quickstart & Local Development

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Docker & Docker Compose (optional for containerized run)

### 2. Environment Configuration
Copy the sample environment file:
```bash
cp .env.example .env
```

### 3. Running the Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

### 4. Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
- Dashboard: [http://localhost:3000](http://localhost:3000)

### 5. Running with Docker Compose
```bash
docker compose up --build
```

### 6. Running Tests
```bash
cd backend
.venv/bin/pytest tests
```

---

## Security Foundation Interfaces

1. **`AgentAction`**: Standardized schema capturing agent ID, task, action verb, target resource, parameters, and execution context.
2. **`ActionContext`**: Session history, permissions, and environment metadata.
3. **`PolicyDecision`**: Deterministic rule outcome (ALLOW / BLOCK, reason, risk score, matched rule ID).
4. **`IntentAnalysis`**: Semantic intent extraction, confidence score, risk indicators, and explanation from NVIDIA Nemotron.
5. **`SecurityDecision`**: Fused final security verdict combining deterministic boundary rules and AI intent reasoning.
6. **`ModelProvider`**: Provider abstraction enabling seamless switching between NVIDIA NIM, NVIDIA Cloud API, and local mock providers.
7. **`ActionInterceptor`**: Interception pipeline coordinating policy evaluation, AI analysis, decision synthesis, and structured JSON audit logging.

---

## License
MIT License. See [LICENSE](LICENSE) for details.
