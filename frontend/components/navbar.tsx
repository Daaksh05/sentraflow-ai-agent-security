"use client";

import { useEffect, useState } from "react";
import { Shield, Cpu, Activity, AlertCircle, ExternalLink, Search, Terminal, Lock } from "lucide-react";
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
    const interval = setInterval(poll, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-black/85 border-b border-zinc-800/80 px-6 py-3 transition-colors">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Left: NVIDIA Logo + SentraFlow Brand */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3 cursor-pointer group">
            {/* NVIDIA Green Icon Badge */}
            <div className="w-8 h-8 rounded-lg bg-black border border-[#76B900]/60 flex items-center justify-center shadow-nvidia-sm group-hover:shadow-nvidia-glow transition-all">
              <svg className="w-5 h-5 text-[#76B900]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M7.78 3.5a9.5 9.5 0 0 0-4.63 2.15 9.25 9.25 0 0 0-2.6 4.93C.18 12.1-.06 13.7.02 15.3c.18 3.6 2.06 6.84 5.07 8.7 1.08.66 2.3.97 3.56.97.8 0 1.6-.14 2.37-.41a8.4 8.4 0 0 0 3.73-2.67 9.8 9.8 0 0 0 2-4.42 12.8 12.8 0 0 0-.25-5.91 10.7 10.7 0 0 0-3.32-5.46 9.68 9.68 0 0 0-5.4-2.5zm-.05 2.1c1.23.03 2.45.38 3.52 1.02a7.6 7.6 0 0 1 2.7 2.8 8.6 8.6 0 0 1 1.04 4.09c0 1.48-.43 2.93-1.25 4.15a7.57 7.57 0 0 1-3.23 2.65 6.42 6.42 0 0 1-4.7-.06 6.8 6.8 0 0 1-3.34-3.1 7.7 7.7 0 0 1-.87-4.14 7.8 7.8 0 0 1 1.76-4.52 7.1 7.1 0 0 1 4.37-2.9zm.08 2.2a5.45 5.45 0 0 0-3.4 1.25 5.66 5.66 0 0 0-1.78 3.44c-.22 1.25-.03 2.53.53 3.63a5.2 5.2 0 0 0 2.65 2.3 4.54 4.54 0 0 0 3.53-.16 5.2 5.2 0 0 0 2.5-2.4 5.76 5.76 0 0 0 .5-3.6 5.57 5.57 0 0 0-1.84-3.3 4.9 4.9 0 0 0-2.7-1.16z" />
              </svg>
            </div>

            <div className="flex flex-col">
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-white flex items-center">
                  Sentra<span className="text-[#76B900]">Flow</span>
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-[#76B900]/15 text-[#8ce000] border border-[#76B900]/30 shadow-nvidia-sm">
                  Nemotron 3.5
                </span>
              </div>
              <span className="text-[11px] text-zinc-400 font-medium">
                AI Agent Security & Control Plane
              </span>
            </div>
          </div>

          {/* Navigation Links matching NVIDIA Build */}
          <nav className="hidden lg:flex items-center space-x-1 text-xs font-medium text-zinc-300">
            <a
              href="#overview"
              className="px-3 py-1.5 rounded-md hover:text-white hover:bg-zinc-800/60 transition"
            >
              Overview
            </a>
            <a
              href="#models"
              className="px-3 py-1.5 rounded-md hover:text-white hover:bg-zinc-800/60 transition flex items-center space-x-1"
            >
              <span>NVIDIA Models</span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#76B900]"></span>
            </a>
            <a
              href="#simulator"
              className="px-3 py-1.5 rounded-md hover:text-white hover:bg-zinc-800/60 transition"
            >
              Attack Simulator
            </a>
            <a
              href="#trajectory"
              className="px-3 py-1.5 rounded-md hover:text-white hover:bg-zinc-800/60 transition"
            >
              Trajectory Monitor
            </a>
            <a
              href="#policies"
              className="px-3 py-1.5 rounded-md hover:text-white hover:bg-zinc-800/60 transition"
            >
              Policies
            </a>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="px-3 py-1.5 rounded-md text-zinc-400 hover:text-[#76B900] hover:bg-zinc-800/60 transition flex items-center space-x-1"
            >
              <span>API Specs</span>
              <ExternalLink className="w-3 h-3 ml-0.5" />
            </a>
          </nav>
        </div>

        {/* Right: Search + Live Status */}
        <div className="flex items-center space-x-3">
          {/* Quick Search matching NVIDIA Build ⌘K */}
          <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-zinc-900/90 border border-zinc-800 text-xs text-zinc-400">
            <Search className="w-3.5 h-3.5 text-zinc-500" />
            <span>Search security policies...</span>
            <kbd className="px-1.5 py-0.5 text-[10px] bg-zinc-800 text-zinc-400 rounded border border-zinc-700 font-mono">
              ⌘K
            </kbd>
          </div>

          {/* Model Status Pill */}
          <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-black border border-zinc-800 text-xs">
            <Cpu className="w-3.5 h-3.5 text-[#76B900]" />
            <span className="font-mono text-zinc-300 text-[11px]">nemotron-3.5-bolt-e4b</span>
          </div>

          {/* Live API Health Badge */}
          <div
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all ${
              isLive
                ? "bg-[#76B900]/10 border-[#76B900]/40 text-[#8ce000] shadow-nvidia-sm"
                : "bg-amber-500/10 border-amber-500/30 text-amber-400"
            }`}
          >
            {isLive ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#76B900] opacity-80"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#76B900]"></span>
                </span>
                <span>NIM Active</span>
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                <span>Backend Offline</span>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
