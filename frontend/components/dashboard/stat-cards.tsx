import { ShieldCheck, Cpu, Terminal, Lock, Activity, Zap } from "lucide-react";

export function StatCards() {
  const stats = [
    {
      label: "Autonomous Boundary",
      value: "Deterministic",
      desc: "Zero-Trust Policy Supremacy",
      detail: "Hard blocks on /etc/shadow, .env, root deletion",
      icon: Lock,
      color: "text-[#76B900]",
      badge: "Zero False Negatives",
      badgeColor: "bg-[#76B900]/15 text-[#8ce000] border-[#76B900]/30",
    },
    {
      label: "Semantic AI Reasoner",
      value: "Nemotron 3.5 Bolt",
      desc: "NVIDIA NIM Inference Microservice",
      detail: "8B Compact text model for agentic intent",
      icon: Cpu,
      color: "text-[#76B900]",
      badge: "Live NVIDIA API",
      badgeColor: "bg-[#76B900]/15 text-[#8ce000] border-[#76B900]/30",
    },
    {
      label: "Control Mechanism",
      value: "Pre-Execution Gate",
      desc: "Interception Pipeline",
      detail: "Evaluates action BEFORE execution in external tool",
      icon: ShieldCheck,
      color: "text-cyan-400",
      badge: "Real-Time Defense",
      badgeColor: "bg-cyan-500/15 text-cyan-300 border-cyan-500/30",
    },
    {
      label: "Behavioral Monitor",
      value: "Trajectory Engine",
      desc: "Multi-Step Attack Detection",
      detail: "Halts lateral exploration & delayed data egress",
      icon: Activity,
      color: "text-amber-400",
      badge: "Session Memory",
      badgeColor: "bg-amber-500/15 text-amber-300 border-amber-500/30",
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, idx) => {
        const Icon = stat.icon;
        return (
          <div
            key={idx}
            className="group relative p-5 rounded-2xl bg-zinc-950/70 border border-zinc-800/80 backdrop-blur-md hover:border-[#76B900]/50 transition-all duration-300 hover:shadow-nvidia-sm overflow-hidden"
          >
            {/* Top glowing ambient highlight on hover */}
            <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-[#76B900]/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

            <div className="flex items-center justify-between mb-3">
              <span className="text-[11px] font-bold text-zinc-400 uppercase tracking-widest font-mono">
                {stat.label}
              </span>
              <div className="p-2 rounded-xl bg-black border border-zinc-800/80 group-hover:border-[#76B900]/40 transition">
                <Icon className={`w-4 h-4 ${stat.color}`} />
              </div>
            </div>

            <div className="text-xl font-extrabold text-white tracking-tight mb-1 group-hover:text-white transition">
              {stat.value}
            </div>
            
            <div className="text-xs text-zinc-400 font-medium mb-3">
              {stat.desc}
            </div>

            <div className="pt-3 border-t border-zinc-900 flex items-center justify-between text-[11px]">
              <span className="text-zinc-500 truncate max-w-[170px]">{stat.detail}</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${stat.badgeColor}`}>
                {stat.badge}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
