import {
  ActionContext,
  AgentAction,
  AttackScenario,
  BatchAgentActionRequest,
  BatchSecurityDecisionResponse,
  PolicySynthesizeResponse,
  RedTeamRunResponse,
  SecurityDecision,
  SystemHealth,
} from "@/types/security";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function checkBackendHealth(): Promise<SystemHealth> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Health check failed with status: ${response.status}`);
  }
  return response.json();
}

export async function analyzeAgentAction(action: AgentAction): Promise<SecurityDecision> {
  const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(action),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Security evaluation failed (${response.status}): ${errorBody}`);
  }

  return response.json();
}

export async function analyzeBatchActions(
  batchRequest: BatchAgentActionRequest
): Promise<BatchSecurityDecisionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/analyze/batch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(batchRequest),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Batch security evaluation failed (${response.status}): ${errorBody}`);
  }

  return response.json();
}

export async function synthesizePolicy(
  prompt: string,
  autoActivate: boolean = true
): Promise<PolicySynthesizeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/policies/synthesize`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ prompt, auto_activate: autoActivate }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Policy synthesis failed (${response.status}): ${errorBody}`);
  }

  return response.json();
}

export async function getActivePolicies(): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/policies/active`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch active policies: ${response.status}`);
  }
  return response.json();
}

export async function getRedTeamScenarios(): Promise<AttackScenario[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/redteam/scenarios`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Failed to fetch red team scenarios: ${response.status}`);
  }
  return response.json();
}

export async function runRedTeamAttack(scenarioId: string): Promise<RedTeamRunResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/redteam/run`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ scenario_id: scenarioId }),
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`Red team attack simulation failed (${response.status}): ${errorBody}`);
  }

  return response.json();
}
