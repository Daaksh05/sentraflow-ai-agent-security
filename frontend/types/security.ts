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

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

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
  task_relevance?: number;
  confidence: number;
  risk_indicators: string[];
  risk_score: number;
  risk_level?: RiskLevel;
  explanation: string;
  recommended_action?: DecisionOutcome;
  model_provider: string;
  model_name?: string;
}

export type TrajectoryClassification =
  | "NORMAL"
  | "SUSPICIOUS"
  | "ESCALATING"
  | "CREDENTIAL_ACCESS"
  | "DATA_EXFILTRATION"
  | "TASK_DRIFT"
  | "REPEATED_ATTACK"
  | "MIXED";

export interface TrajectoryStep {
  step_index: number;
  action: string;
  resource: string;
  action_type?: string;
  decision?: DecisionOutcome;
  risk_score?: number;
  risk_level?: RiskLevel;
  task_relevance?: number;
  timestamp?: string;
}

export interface BehaviorAnalysis {
  session_id: string;
  behavior_risk_score: number;
  behavior_risk_level: RiskLevel;
  trajectory_classification: TrajectoryClassification;
  behavior_indicators: string[];
  explanation: string;
  action_count: number;
  trajectory?: TrajectoryStep[];
}

export interface SecurityDecision {
  decision: DecisionOutcome;
  risk_score: number;
  risk_level?: RiskLevel;
  intent: string;
  reason: string;
  analysis_source: string;
  enforcement_mode?: string;
  request_id: string;
  policy_decision?: PolicyDecision;
  intent_analysis?: IntentAnalysis;
  behavior_analysis?: BehaviorAnalysis;
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
  behavior_analysis?: BehaviorAnalysis;
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

