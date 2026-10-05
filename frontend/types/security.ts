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

export type EnforcementMode = "ENFORCE" | "AUDIT_ONLY";

export interface PreviousAction {
  action: string;
  resource: string;
  decision: string;
  timestamp?: string;
}

export interface ActionContext {
  agent_id?: string;
  task?: string;
  requested_action?: string;
  target_resource?: string;
  session_id?: string;
  previous_actions?: PreviousAction[];
  permissions?: string[];
  environment_variables?: Record<string, string>;
  metadata?: Record<string, any>;
}

export interface AgentAction {
  agent_id: string;
  task: string;
  action: string;
  resource: string;
  parameters?: Record<string, any>;
  context?: Record<string, any>;
  action_context?: ActionContext;
  action_type?: ActionType;
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
  enforcement_mode?: string;
  request_id: string;
  policy_decision?: PolicyDecision;
  intent_analysis?: IntentAnalysis;
  evaluated_at: string;
}

export interface BatchAgentActionRequest {
  actions: AgentAction[];
  context?: ActionContext;
  stop_on_first_block?: boolean;
}

export interface BatchSecurityDecisionResponse {
  overall_decision: DecisionOutcome;
  total_actions: number;
  allowed_count: number;
  blocked_count: number;
  highest_risk_score: number;
  decisions: SecurityDecision[];
  blocked_action_index?: number;
  enforcement_mode: string;
  evaluated_at: string;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp?: string;
}
