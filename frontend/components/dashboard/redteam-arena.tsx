"use client";

import { useState, useEffect } from "react";
import {
  Flame,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Play,
  RefreshCw,
  Terminal,
  Cpu,
  Layers,
  Lock,
  Target,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
  Bug,
  Radio,
} from "lucide-react";
import { getRedTeamScenarios, runRedTeamAttack } from "@/lib/api";
import { AttackScenario, RedTeamRunResponse } from "@/types/security";

export function RedTeamArena() {
  const [scenarios, setScenarios] = useState<AttackScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<AttackScenario | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<RedTeamRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    loadScenarios();
  }, []);

  const loadScenarios = async () => {
    try {
      const data = await getRedTeamScenarios();
      setScenarios(data);
      if (data.length > 0) {
        setSelectedScenario(data[0]);
      }
    } catch {
      // Fallback
    }
  };

  const handleRunAttack = async (scenarioId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await runRedTeamAttack(scenarioId);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Failed to execute red team exploit");
    } finally {
      setLoading(false);
    }
  };

  const copyResultJson = () => {
    if (!result) return;
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
      {/* Left: Adversarial Exploit Launcher */}
      <div className="lg:col-span-6 space-y-6">
        <div className="p-6 rounded-2xl bg-zinc-950/85 border border-zinc-800 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-zinc-900">
            <div>
              <div className="flex items-center space-x-2">
                <Flame className="w-4 h-4 text-rose-500 animate-pulse" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Adversarial Red Team Exploits
                </h3>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Simulate complex prompt injections, steganographic payloads, and C2 reverse shells.
              </p>
            </div>
            <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
              Adversarial Arena
            </span>
          </div>

          {/* Scenario Cards */}
          <div className="space-y-2.5 mb-6">
            <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest font-mono">
              Curated Exploit Scenarios
            </label>

            <div className="grid grid-cols-1 gap-2.5">
              {scenarios.map((sc) => (
                <button
                  key={sc.id}
                  type="button"
                  onClick={() => {
                    setSelectedScenario(sc);
                    setResult(null);
                  }}
                  className={`text-left p-3 rounded-xl border text-xs transition-all duration-200 group ${
                    selectedScenario?.id === sc.id
                      ? "border-rose-500 bg-rose-500/10 text-white shadow-red-glow"
                      : "border-zinc-800/80 bg-black/60 text-zinc-300 hover:border-zinc-700 hover:bg-zinc-900/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-white group-hover:text-rose-300 transition">
                      {sc.name}
                    </span>
                    <span className="text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase border bg-rose-500/20 text-rose-300 border-rose-500/40">
                      {sc.severity}
                    </span>
                  </div>

                  <p className="text-[11px] text-zinc-400 mb-2">
                    {sc.description}
                  </p>

                  <div className="flex items-center space-x-3 text-[10px] font-mono text-zinc-500">
                    <span className="text-zinc-400 font-semibold">{sc.owasp_tag}</span>
                    <span>•</span>
                    <span className="text-rose-400">{sc.mitre_tactic}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Selected Payload Preview & Launch Button */}
          {selectedScenario && (
            <div className="space-y-4 pt-2 border-t border-zinc-900">
              <div className="p-3.5 rounded-xl bg-black border border-zinc-800 space-y-1.5">
                <span className="text-[10px] font-mono uppercase font-bold text-zinc-500 block">
                  Adversarial Technique
                </span>
                <p className="text-xs text-rose-300 font-medium">
                  {selectedScenario.adversarial_technique}
                </p>
                <div className="pt-2 text-[11px] font-mono text-zinc-400 flex items-center space-x-2">
                  <span className="text-zinc-500">Target Action:</span>
                  <span className="text-white font-bold">{selectedScenario.action.action}</span>
                  <span className="text-zinc-500 truncate max-w-[250px]">{selectedScenario.action.resource}</span>
                </div>
              </div>

              <button
                onClick={() => handleRunAttack(selectedScenario.id)}
                disabled={loading}
                className="w-full py-3 px-4 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-extrabold text-sm flex items-center justify-center space-x-2 transition shadow-red-glow disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-white" />
                    <span>Executing Exploit & Evaluating Defense...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-white text-white" />
                    <span>Launch Exploit Against SentraFlow</span>
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Right: Blue Team Interception Telemetry */}
      <div className="lg:col-span-6 space-y-6">
        <div className="p-6 rounded-2xl bg-zinc-950/85 border border-zinc-800 shadow-2xl backdrop-blur-xl h-full flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-zinc-900">
              <div>
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-[#76B900]" />
                  <h3 className="text-base font-bold text-white tracking-tight">
                    Blue Team Defense Telemetry
                  </h3>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Multi-phase defense analysis: Policy supremacy vs. Nemotron reasoning vs. Trajectory.
                </p>
              </div>

              {result && (
                <button
                  onClick={copyResultJson}
                  className="flex items-center space-x-1 text-xs text-zinc-400 hover:text-white px-2.5 py-1 rounded-lg bg-zinc-900 border border-zinc-800 transition"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-[#76B900]" />
                      <span className="text-[#76B900]">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Log</span>
                    </>
                  )}
                </button>
              )}
            </div>

            {error && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold">Simulation Error</div>
                  <div>{error}</div>
                </div>
              </div>
            )}

            {!result && !error && !loading && (
              <div className="py-24 text-center border border-dashed border-zinc-800/80 rounded-2xl bg-black/40">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-black border border-zinc-800 flex items-center justify-center text-rose-500 shadow-red-glow">
                  <Radio className="w-8 h-8" />
                </div>
                <div className="text-base font-bold text-white">
                  Arena Standing By
                </div>
                <div className="text-xs text-zinc-400 max-w-sm mx-auto mt-2 leading-relaxed">
                  Select an adversarial attack scenario on the left and click <span className="text-rose-400 font-semibold">"Launch Exploit"</span> to trigger the simulation and observe real-time defense interception.
                </div>
              </div>
            )}

            {result && (
              <div className="space-y-4">
                {/* Attack Thwarted Banner */}
                <div
                  className={`p-4 rounded-xl border flex items-center justify-between transition ${
                    result.attack_thwarted
                      ? "bg-rose-500/15 border-rose-500/40 shadow-red-glow"
                      : "bg-emerald-500/15 border-emerald-500/40 shadow-nvidia-sm"
                  }`}
                >
                  <div className="flex items-center space-x-3.5">
                    {result.attack_thwarted ? (
                      <div className="p-3 rounded-xl bg-rose-500/20 text-rose-400 border border-rose-500/40">
                        <ShieldAlert className="w-7 h-7" />
                      </div>
                    ) : (
                      <div className="p-3 rounded-xl bg-emerald-500/20 text-[#8ce000] border border-emerald-500/40">
                        <ShieldCheck className="w-7 h-7" />
                      </div>
                    )}
                    <div>
                      <div className="text-xs text-zinc-400 font-medium">Attack Simulation Result</div>
                      <div className="text-2xl font-black tracking-tight text-rose-400">
                        {result.attack_thwarted ? "ATTACK THWARTED" : "ACTION ALLOWED"}
                      </div>
                    </div>
                  </div>

                  <span className="text-xs px-2.5 py-1 rounded font-bold font-mono bg-black text-rose-400 border border-rose-500/40 uppercase">
                    Decision: {result.decision.decision}
                  </span>
                </div>

                {/* Defense Stage Attribution */}
                <div className="p-3.5 rounded-xl bg-black border border-zinc-800 space-y-1">
                  <span className="text-[10px] font-mono uppercase font-bold text-zinc-500 block">
                    Intercepting Defense Stage
                  </span>
                  <div className="flex items-center space-x-2 text-sm font-bold text-[#8ce000]">
                    <CheckCircle2 className="w-4 h-4 text-[#76B900]" />
                    <span>{result.defense_stage}</span>
                  </div>
                </div>

                {/* Risk & Alignment Grid */}
                <div className="grid grid-cols-3 gap-2.5 text-xs">
                  <div className="p-3 rounded-xl bg-black border border-zinc-800 text-center">
                    <div className="text-[10px] uppercase font-bold text-zinc-400 font-mono">
                      Threat Risk
                    </div>
                    <div className="text-lg font-black text-rose-400 mt-0.5 font-mono">
                      {result.decision.risk_score}
                      <span className="text-xs text-zinc-600">/100</span>
                    </div>
                    <div className="text-[10px] text-zinc-400 font-semibold uppercase">
                      {result.decision.risk_level || "CRITICAL"}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-black border border-zinc-800 text-center">
                    <div className="text-[10px] uppercase font-bold text-zinc-400 font-mono">
                      MITRE ATT&CK
                    </div>
                    <div className="text-xs font-bold text-amber-400 mt-1 truncate">
                      {result.mitre_tactic.split(":")[0]}
                    </div>
                    <div className="text-[10px] text-zinc-400 font-semibold truncate">
                      {result.mitre_tactic.split(":")[1] || "Execution"}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-black border border-zinc-800 text-center">
                    <div className="text-[10px] uppercase font-bold text-zinc-400 font-mono">
                      OWASP Classification
                    </div>
                    <div className="text-xs font-bold text-cyan-400 mt-1 truncate">
                      {result.owasp_tag.split(" ")[1] || "LLM01"}
                    </div>
                    <div className="text-[10px] text-zinc-400 font-semibold truncate">
                      Guarded
                    </div>
                  </div>
                </div>

                {/* Explanation Rationale */}
                <div className="p-3.5 rounded-xl bg-black border border-zinc-800 space-y-1.5">
                  <span className="text-[10px] font-mono uppercase font-bold text-zinc-500 block">
                    Security Defense Rationale
                  </span>
                  <p className="text-xs text-zinc-300 leading-relaxed font-medium">
                    {result.explanation}
                  </p>
                </div>

                {/* Nemotron Semantic Reasoning */}
                {result.decision.intent_analysis && (
                  <div className="p-3.5 rounded-xl bg-black border border-zinc-800/80 space-y-1">
                    <span className="text-[10px] font-mono uppercase font-bold text-zinc-500 block flex items-center space-x-1">
                      <Cpu className="w-3 h-3 text-[#76B900]" />
                      <span>Nemotron 3.5 Intent Extraction</span>
                    </span>
                    <p className="text-xs text-zinc-400 italic">
                      "{result.decision.intent_analysis.detected_intent}"
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-zinc-900 text-[11px] text-zinc-500 flex items-center justify-between">
            <span className="font-mono">Real-Time Adversarial Interception</span>
            <span className="text-rose-400 font-semibold">Zero-Day Shield Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
