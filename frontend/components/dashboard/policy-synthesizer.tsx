"use client";

import { useState, useEffect } from "react";
import {
  Sparkles,
  Lock,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Play,
  RefreshCw,
  Layers,
  ArrowRight,
  ShieldCheck,
  Code2,
  Copy,
  Check,
} from "lucide-react";
import { synthesizePolicy, getActivePolicies } from "@/lib/api";
import { PolicySynthesizeResponse } from "@/types/security";

const SAMPLE_PROMPTS = [
  "Block all attempts to execute python scripts from /tmp and forbid writes to /etc/",
  "Prohibit any agent from querying customer_pii table and block database drops",
  "Quarantine all external network calls and curl webhooks, but allow local reads",
  "Allow QA agent read-only access to tests/ directory and block file modifications",
];

export function PolicySynthesizer() {
  const [prompt, setPrompt] = useState<string>(SAMPLE_PROMPTS[0]);
  const [loading, setLoading] = useState<boolean>(false);
  const [response, setResponse] = useState<PolicySynthesizeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeRules, setActiveRules] = useState<any[]>([]);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    loadActiveRules();
  }, []);

  const loadActiveRules = async () => {
    try {
      const rules = await getActivePolicies();
      setActiveRules(rules);
    } catch {
      // Graceful fallback
    }
  };

  const handleSynthesize = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await synthesizePolicy(prompt, true);
      setResponse(res);
      await loadActiveRules();
    } catch (err: any) {
      setError(err.message || "Failed to synthesize policy");
    } finally {
      setLoading(false);
    }
  };

  const copyRuleJson = () => {
    if (!response) return;
    navigator.clipboard.writeText(JSON.stringify(response.rule, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
      {/* Left: Input & Prompt Editor */}
      <div className="lg:col-span-6 space-y-6">
        <div className="p-6 rounded-2xl bg-zinc-950/85 border border-zinc-800 shadow-2xl backdrop-blur-xl">
          <div className="flex items-center justify-between mb-4 pb-3 border-b border-zinc-900">
            <div>
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-[#76B900]" />
                <h3 className="text-base font-bold text-white tracking-tight">
                  Text-to-Policy Synthesizer
                </h3>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Powered by NVIDIA Nemotron 3.5 Bolt. Translates natural language into zero-trust regex rules.
              </p>
            </div>
            <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-[#76B900]/15 text-[#8ce000] border border-[#76B900]/30 shadow-nvidia-sm">
              Hot-Reload Active
            </span>
          </div>

          {/* Quick Prompts */}
          <div className="mb-5 space-y-2">
            <label className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest font-mono">
              Sample Security Directives
            </label>
            <div className="grid grid-cols-1 gap-2">
              {SAMPLE_PROMPTS.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setPrompt(p)}
                  className={`text-left p-2.5 rounded-xl border text-xs transition-all ${
                    prompt === p
                      ? "border-[#76B900] bg-[#76B900]/10 text-white"
                      : "border-zinc-800/80 bg-black/50 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700"
                  }`}
                >
                  <span className="font-mono text-[11px]">{p}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Prompt Textarea */}
          <div className="space-y-4 text-xs">
            <div>
              <label className="block text-zinc-400 mb-1.5 font-medium">
                Natural Language Security Constraint
              </label>
              <textarea
                rows={3}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your security rule in plain English..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-black border border-zinc-800 text-zinc-200 focus:outline-none focus:border-[#76B900] focus:ring-1 focus:ring-[#76B900]/30 font-medium transition"
              />
            </div>

            <button
              onClick={handleSynthesize}
              disabled={loading || !prompt.trim()}
              className="w-full py-3 px-4 rounded-xl bg-[#76B900] hover:bg-[#66a000] text-black font-extrabold text-sm flex items-center justify-center space-x-2 transition shadow-nvidia-sm hover:shadow-nvidia-glow disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-black" />
                  <span>Compiling Policy with Nemotron 3.5...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 text-black" />
                  <span>Synthesize & Hot-Reload Policy</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Active Rules Counter & Mini-list */}
        <div className="p-5 rounded-2xl bg-zinc-950/85 border border-zinc-800 text-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
            <span className="font-bold text-white flex items-center space-x-1.5">
              <Lock className="w-3.5 h-3.5 text-[#76B900]" />
              <span>Active Kernel Rules</span>
            </span>
            <span className="text-[11px] font-mono text-[#8ce000]">
              {activeRules.length} Enforced Rules
            </span>
          </div>

          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {activeRules.slice(0, 5).map((rule, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-black/60 border border-zinc-800/80 font-mono text-[11px] flex items-center justify-between"
              >
                <div className="truncate max-w-[280px]">
                  <span className="text-[#8ce000] font-bold mr-1.5">{rule.rule_id}</span>
                  <span className="text-zinc-300">{rule.name}</span>
                </div>
                <span
                  className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    rule.outcome === "BLOCK"
                      ? "bg-rose-500/15 text-rose-300 border border-rose-500/30"
                      : "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
                  }`}
                >
                  {rule.outcome}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Synthesized Rule Output */}
      <div className="lg:col-span-6 space-y-6">
        <div className="p-6 rounded-2xl bg-zinc-950/85 border border-zinc-800 shadow-2xl backdrop-blur-xl h-full flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-zinc-900">
              <div>
                <div className="flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-[#76B900]" />
                  <h3 className="text-base font-bold text-white tracking-tight">
                    Synthesized Zero-Trust Rule
                  </h3>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  Compiled regex patterns, risk tier, and auditable reason.
                </p>
              </div>

              {response && (
                <button
                  onClick={copyRuleJson}
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
                      <span>Copy Rule</span>
                    </>
                  )}
                </button>
              )}
            </div>

            {error && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold">Synthesis Error</div>
                  <div>{error}</div>
                </div>
              </div>
            )}

            {!response && !error && !loading && (
              <div className="py-24 text-center border border-dashed border-zinc-800/80 rounded-2xl bg-black/40">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-black border border-zinc-800 flex items-center justify-center text-[#76B900] shadow-nvidia-sm">
                  <Sparkles className="w-8 h-8" />
                </div>
                <div className="text-base font-bold text-white">
                  Awaiting Directive Input
                </div>
                <div className="text-xs text-zinc-400 max-w-sm mx-auto mt-2 leading-relaxed">
                  Enter a security rule in plain English on the left and click <span className="text-[#8ce000] font-semibold">"Synthesize & Hot-Reload"</span> to watch Nemotron 3.5 compile it into a zero-trust policy.
                </div>
              </div>
            )}

            {response && (
              <div className="space-y-4">
                {/* Active Status Badge */}
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 shadow-nvidia-sm flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 rounded-xl bg-emerald-500/20 text-[#8ce000] border border-emerald-500/40">
                      <ShieldCheck className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="text-xs text-zinc-400 font-medium">Policy Engine Status</div>
                      <div className="text-lg font-black tracking-tight text-[#8ce000]">
                        Hot-Reload Successful
                      </div>
                    </div>
                  </div>

                  <span className="text-xs px-2.5 py-1 rounded font-bold font-mono bg-black text-[#8ce000] border border-[#76B900]/40">
                    Rule ID: {response.rule.rule_id}
                  </span>
                </div>

                {/* Rule Breakdown */}
                <div className="space-y-2.5 text-xs">
                  <div className="p-3.5 rounded-xl bg-black border border-zinc-800">
                    <span className="text-[10px] uppercase font-mono text-zinc-500 block mb-0.5">
                      Rule Title
                    </span>
                    <span className="font-bold text-white text-sm">
                      {response.rule.name}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2.5">
                    <div className="p-3.5 rounded-xl bg-black border border-zinc-800">
                      <span className="text-[10px] uppercase font-mono text-zinc-500 block mb-1">
                        Resource Regex Pattern
                      </span>
                      <code className="text-[#8ce000] font-mono text-[11px] block break-all">
                        {response.rule.resource_pattern}
                      </code>
                    </div>

                    <div className="p-3.5 rounded-xl bg-black border border-zinc-800">
                      <span className="text-[10px] uppercase font-mono text-zinc-500 block mb-1">
                        Action Verb Regex
                      </span>
                      <code className="text-cyan-400 font-mono text-[11px] block break-all">
                        {response.rule.action_pattern}
                      </code>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2.5">
                    <div className="p-3 rounded-xl bg-black border border-zinc-800 flex items-center justify-between">
                      <span className="text-zinc-400">Enforcement Outcome:</span>
                      <span
                        className={`font-mono font-bold px-2 py-0.5 rounded text-[10px] border ${
                          response.rule.decision === "BLOCK"
                            ? "bg-rose-500/15 text-rose-300 border-rose-500/30"
                            : "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
                        }`}
                      >
                        {response.rule.decision}
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-black border border-zinc-800 flex items-center justify-between">
                      <span className="text-zinc-400">Calculated Risk Score:</span>
                      <span className="font-mono font-bold text-white">
                        {response.rule.risk_score}/100
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-black border border-zinc-800 space-y-1">
                    <span className="text-[10px] uppercase font-mono text-zinc-500 block">
                      Auditable Enforcement Reason
                    </span>
                    <p className="text-zinc-300 leading-relaxed font-medium">
                      {response.rule.reason}
                    </p>
                  </div>

                  {response.rule.explanation && (
                    <div className="p-3.5 rounded-xl bg-black border border-zinc-800/80 text-zinc-400 space-y-1">
                      <span className="text-[10px] uppercase font-mono text-zinc-500 block">
                        Nemotron Technical Logic
                      </span>
                      <p className="text-[11px] leading-relaxed">
                        {response.rule.explanation}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="mt-6 pt-4 border-t border-zinc-900 text-[11px] text-zinc-500 flex items-center justify-between">
            <span className="font-mono">Model: {response?.model_name || "nvidia/nemotron-3.5-bolt-e4b"}</span>
            <span className="text-[#76B900]">Instant Hot-Reload Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
