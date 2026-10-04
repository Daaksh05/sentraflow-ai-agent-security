import { ShieldCheck, Cpu, Terminal, Lock } from "lucide-react";

export function StatCards() {
  const stats = [
    {
      label: "Control Boundary",
      value: "Deterministic",
      desc: "Strict Policy & Boundary Rules",
      icon: Lock,
      color: "text-sentra-400",
      bgColor: "bg-sentra-500/10",
    },
    {
      label: "AI Reasoner",
      value: "NVIDIA Nemotron",
      desc: "Intent & Risk Semantics",
      icon: Cpu,
      color: "text-nvidia-green",
      bgColor: "bg-emerald-500/10",
    },
    {
      label: "Interception Mode",
      value: "Pre-Execution",
      desc: "Block Before Invocation",
      icon: ShieldCheck,
      color: "text-cyan-400",
      bgColor: "bg-cyan-500/10",
    },
    {
      label: "Audit Engine",
      value: "Structured JSON",
      desc: "Traceable Request Identifiers",
      icon: Terminal,
      color: "text-indigo-400",
      bgColor: "bg-indigo-500/10",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, idx) => {
        const Icon = stat.icon;
        return (
          <div
            key={idx}
            className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm hover:border-slate-700/80 transition duration-200 shadow-sm"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                {stat.label}
              </span>
              <div className={`p-2 rounded-xl ${stat.bgColor} ${stat.color}`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            <div className="text-xl font-bold text-white mb-1">{stat.value}</div>
            <div className="text-xs text-slate-400">{stat.desc}</div>
          </div>
        );
      })}
    </div>
  );
}
