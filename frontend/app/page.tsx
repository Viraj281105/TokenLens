"use client";

import MetricsPanel from "@/components/MetricsPanel";
import ChatPlayground from "@/components/ChatPlayground";
import CostChart from "@/components/CostChart";
import {
  Layers,
  Cpu,
  Database,
  Route,
  BarChart3,
  GitBranch,
  ExternalLink,
  Shield,
} from "lucide-react";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="border-b border-zinc-800/50 bg-zinc-950/50 backdrop-blur-xl sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg animate-pulse-glow">
                <Layers className="w-5 h-5 text-white" aria-hidden="true" />
              </div>
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight gradient-text">
                TokenLens
              </h1>
              <p className="text-[10px] text-zinc-500 -mt-0.5 font-medium tracking-wider uppercase">
                LLM Cost Optimizer
              </p>
            </div>
          </div>

          <nav className="flex items-center gap-3" aria-label="Header navigation">
            <a
              href="/docs"
              className="text-xs text-zinc-400 hover:text-violet-400 transition-colors focus-ring px-3 py-1.5 rounded-lg"
              aria-label="API Documentation"
            >
              <span className="hidden sm:inline">API Docs</span>
              <ExternalLink className="w-4 h-4 sm:hidden" aria-hidden="true" />
            </a>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-zinc-400 hover:text-foreground transition-colors focus-ring p-2 rounded-lg"
              aria-label="GitHub repository"
            >
              <GitBranch className="w-4 h-4" aria-hidden="true" />
            </a>
          </nav>
        </div>
      </header>

      {/* ── Main Content ────────────────────────────────────────── */}
      <main id="main-content" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Hero */}
        <section className="text-center py-6 animate-fade-in" aria-label="Hero section">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-3">
            <span className="gradient-text">Cut LLM Costs</span>{" "}
            <span className="text-foreground">by up to 60%</span>
          </h2>
          <p className="text-zinc-400 max-w-2xl mx-auto leading-relaxed">
            Four-layer intelligent middleware: prompt compression, semantic caching,
            complexity routing, and real-time analytics — all powered by Google Gemini.
          </p>
        </section>

        {/* Pipeline Visualization */}
        <section
          className="grid grid-cols-2 md:grid-cols-4 gap-3 animate-fade-in"
          aria-label="Optimization pipeline layers"
        >
          {[
            {
              icon: Cpu,
              label: "Compress",
              desc: "TF-IDF extraction",
              color: "violet",
            },
            {
              icon: Database,
              label: "Cache",
              desc: "FAISS similarity",
              color: "blue",
            },
            {
              icon: Route,
              label: "Route",
              desc: "Model selection",
              color: "amber",
            },
            {
              icon: BarChart3,
              label: "Track",
              desc: "Cost analytics",
              color: "emerald",
            },
          ].map((layer, i) => {
            const Icon = layer.icon;
            const bgClass = `bg-${layer.color}-500/10`;
            const borderClass = `border-${layer.color}-500/20`;
            const textClass = `text-${layer.color}-400`;
            return (
              <div
                key={layer.label}
                className="glass-card p-4 text-center group relative"
              >
                <div className="flex justify-center mb-2">
                  <div
                    className={`p-2.5 rounded-xl ${bgClass} ${borderClass} border transition-transform group-hover:scale-110`}
                  >
                    <Icon className={`w-5 h-5 ${textClass}`} aria-hidden="true" />
                  </div>
                </div>
                <p className="font-semibold text-sm">{layer.label}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{layer.desc}</p>
                <span className="absolute -top-2 -left-2 w-5 h-5 rounded-full bg-zinc-800 border border-zinc-700 text-[10px] font-bold flex items-center justify-center text-zinc-400">
                  {i + 1}
                </span>
              </div>
            );
          })}
        </section>

        {/* Metrics */}
        <MetricsPanel />

        {/* Two-column: Playground + Chart */}
        <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
          <div className="xl:col-span-3">
            <ChatPlayground />
          </div>
          <div className="xl:col-span-2">
            <CostChart />
          </div>
        </div>

        {/* Security badge */}
        <section className="glass-card p-4 flex items-center gap-3 text-sm text-zinc-400" aria-label="Security information">
          <Shield className="w-5 h-5 text-emerald-400 shrink-0" aria-hidden="true" />
          <p>
            <strong className="text-zinc-300">Enterprise-grade security:</strong>{" "}
            API key auth, rate limiting (60 req/min), input validation, CORS protection,
            and Secret Manager integration. No secrets in code or logs.
          </p>
        </section>
      </main>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer className="border-t border-zinc-800/50 py-6 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-zinc-500 gap-2">
          <p>
            © 2026 TokenLens — Built for{" "}
            <strong className="text-zinc-400">Google PromptWars</strong>
          </p>
          <p className="flex items-center gap-1.5">
            Powered by
            <span className="font-semibold text-zinc-400">Google Gemini</span>
            ·
            <span className="text-zinc-400">Cloud Run</span>
          </p>
        </div>
      </footer>
    </div>
  );
}
