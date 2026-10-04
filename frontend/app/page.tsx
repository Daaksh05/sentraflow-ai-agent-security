import { Navbar } from "@/components/navbar";
import { StatCards } from "@/components/dashboard/stat-cards";
import { InterceptorTester } from "@/components/dashboard/interceptor-tester";
import { ArrowDown, Cpu, Shield, Zap, Lock, Terminal } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Hero Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-800/60">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              AI Agent Security & Control Center
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Real-time interception layer sitting between autonomous AI agents and external tools, APIs, and systems.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-sentra-500/10 text-sentra-400 border border-sentra-500/30">
              <Zap className="w-3.5 h-3.5 mr-1" />
              Pre-Execution Interception
            </span>
          </div>
        </div>

        {/* Architecture Flow Banner */}
        <div className="p-5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900/90 to-sentra-950/40 border border-slate-800 shadow-md">
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center space-x-2">
            <Lock className="w-3.5 h-3.5 text-sentra-400" />
            <span>Core Product Interception Pipeline</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs items-center">
            <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
              <div className="text-slate-400 font-mono text-[10px]">Step 1</div>
              <div className="font-semibold text-white mt-0.5">Autonomous Agent</div>
              <div className="text-[11px] text-slate-500">Decides on action</div>
            </div>

            <div className="hidden md:flex justify-center text-slate-600">
              <ArrowDown className="w-4 h-4 -rotate-90 text-sentra-400" />
            </div>

            <div className="p-3 rounded-xl bg-sentra-950/60 border border-sentra-800/80 text-center ring-1 ring-sentra-500/30">
              <div className="text-sentra-400 font-mono text-[10px] font-bold">Step 2 • SentreFlow</div>
              <div className="font-bold text-white mt-0.5">Policy + Nemotron</div>
              <div className="text-[11px] text-sentra-300/80">Deterministic evaluation</div>
            </div>

            <div className="hidden md:flex justify-center text-slate-600">
              <ArrowDown className="w-4 h-4 -rotate-90 text-sentra-400" />
            </div>

            <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
              <div className="text-slate-400 font-mono text-[10px]">Step 3</div>
              <div className="font-semibold text-white mt-0.5">ALLOW / BLOCK</div>
              <div className="text-[11px] text-slate-500">External tool gated</div>
            </div>
          </div>
        </div>

        {/* Stat Cards */}
        <StatCards />

        {/* Interactive Interceptor Tester */}
        <InterceptorTester />
      </main>

      <footer className="border-t border-slate-800/80 py-4 px-6 mt-12 bg-slate-950/60 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>SentreFlow — AI Agent Security & Control Platform • MIT License</div>
          <div className="flex items-center space-x-4">
            <span>FastAPI Backend</span>
            <span>Next.js Dashboard</span>
            <span>NVIDIA Nemotron Integration</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
