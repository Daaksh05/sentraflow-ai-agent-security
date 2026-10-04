export type ActionType =
  | "READ"
  | "WRITE"
  | "EXECUTE"
  | "NETWORK_CALL"
  | "AUTH"
  | "DELETE"
  | "SYSTEM_CONFIG"
  | "OTHER";

export type DecisionOutcome = "ALLOW" | "BLOCK" | "REQUIRE_APPROVAL" | "ESCALATE";

export interface AgentAction {
  agent_id: string;
  task: string;
  action: string;
  resource: string;
  parameters?: Record<string, any>;
  context?: Record<string, any>;
  timestamp?: string;
}

export interface PolicyDecision {
  decision: DecisionOutcome;
  reason: string;
  risk_score: number;
  policy_id?: string;
  policy_name?: string;
  rule_matched?: string;
}

export interface IntentAnalysis {
  detected_intent: string;
  confidence: number;
  risk_indicators: string[];
  risk_score: number;
  explanation: string;
  model_provider: string;
  model_name?: string;
}

export interface SecurityDecision {
  decision: DecisionOutcome;
  risk_score: number;
  intent: string;
  reason: string;
  analysis_source: string;
  request_id: string;
  policy_decision?: PolicyDecision;
  intent_analysis?: IntentAnalysis;
  evaluated_at: string;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp?: string;
}
