"use client";

import { useEffect, useState } from "react";
import { Shield, Cpu, Activity, CheckCircle2, AlertCircle } from "lucide-react";
import { checkBackendHealth } from "@/lib/api";
import { SystemHealth } from "@/types/security";

export function Navbar() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isLive, setIsLive] = useState<boolean>(false);

  useEffect(() => {
    async function poll() {
      try {
        const res = await checkBackendHealth();
        setHealth(res);
        setIsLive(true);
      } catch {
        setIsLive(false);
      }
    }
    poll();
    const interval = setInterval(poll, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/70 border-b border-slate-800/80 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-sentra-600 to-cyan-400 text-white shadow-lg shadow-sentra-600/20">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-xl tracking-tight text-white">SentreFlow</span>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-sentra-500/10 text-sentra-400 border border-sentra-500/20">
                Security Layer
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous AI Agent Control & Policy Engine</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300">
            <Cpu className="w-4 h-4 text-nvidia-green" />
            <span>NVIDIA Nemotron Reasoning</span>
          </div>

          <div
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium border ${
              isLive
                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                : "bg-amber-500/10 border-amber-500/30 text-amber-400"
            }`}
          >
            {isLive ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span>API v1 Online</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Connecting API...</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
