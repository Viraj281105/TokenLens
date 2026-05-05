"use client";

import { useEffect, useState } from "react";
import {
  Zap,
  DollarSign,
  Target,
  Activity,
  TrendingUp,
  TrendingDown,
} from "lucide-react";

interface Stats {
  total_requests: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_cost_usd: number;
  cost_saved_usd: number;
  cache_hits: number;
  cache_hit_rate: number;
  compression_savings_tokens: number;
  avg_efficiency_score: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export default function MetricsPanel() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/stats`, {
          headers: {
            "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || 'tokenlens2026',
          },
        });
        if (res.ok) {
          setStats(await res.json());
        }
      } catch {
        // Silently fail — stats will show defaults
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const cards = [
    {
      id: "tokens-saved",
      label: "Tokens Saved",
      value: stats?.compression_savings_tokens ?? 0,
      format: (v: number) => v.toLocaleString(),
      icon: Zap,
      color: "text-violet-400",
      bgColor: "bg-violet-500/10",
      borderColor: "border-violet-500/20",
      trend: stats?.avg_efficiency_score ?? 0,
      trendLabel: "efficiency",
    },
    {
      id: "cost-saved",
      label: "Cost Saved",
      value: stats?.cost_saved_usd ?? 0,
      format: (v: number) => `$${v.toFixed(4)}`,
      icon: DollarSign,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/20",
      trend: stats?.cost_saved_usd ?? 0,
      trendLabel: "saved",
    },
    {
      id: "cache-hit-rate",
      label: "Cache Hit Rate",
      value: stats?.cache_hit_rate ?? 0,
      format: (v: number) => `${v.toFixed(1)}%`,
      icon: Target,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/20",
      trend: stats?.cache_hits ?? 0,
      trendLabel: "hits",
    },
    {
      id: "total-requests",
      label: "Requests",
      value: stats?.total_requests ?? 0,
      format: (v: number) => v.toLocaleString(),
      icon: Activity,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/20",
      trend: stats?.total_tokens_in ?? 0,
      trendLabel: "tokens in",
    },
  ];

  return (
    <section aria-label="Key metrics overview" className="stagger-children">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              id={card.id}
              className={`glass-card p-5 relative overflow-hidden group`}
              role="status"
              aria-label={`${card.label}: ${card.format(card.value)}`}
            >
              {/* Shimmer overlay on load */}
              {loading && (
                <div className="absolute inset-0 animate-shimmer rounded-xl" />
              )}

              <div className="flex items-start justify-between mb-3">
                <div
                  className={`p-2.5 rounded-xl ${card.bgColor} ${card.borderColor} border transition-transform group-hover:scale-110`}
                >
                  <Icon className={`w-5 h-5 ${card.color}`} aria-hidden="true" />
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  {card.trend > 0 ? (
                    <TrendingUp className="w-3 h-3 text-emerald-400" aria-hidden="true" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-zinc-500" aria-hidden="true" />
                  )}
                  <span className="sr-only">Trend:</span>
                  <span>
                    {typeof card.trend === "number"
                      ? card.trend.toLocaleString()
                      : card.trend}{" "}
                    {card.trendLabel}
                  </span>
                </div>
              </div>

              <p className="text-2xl font-bold tracking-tight animate-count-up">
                {loading ? "—" : card.format(card.value)}
              </p>
              <p className="text-sm text-muted-foreground mt-1">{card.label}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
