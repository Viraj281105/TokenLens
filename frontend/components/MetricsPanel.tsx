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
import CountUp from "react-countup";
import { Sparklines, SparklinesLine } from "react-sparklines";

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

const API_BASE = "";

export default function MetricsPanel() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  // Mock data for sparklines
  const mockSparklineData1 = [5, 10, 5, 20, 8, 15, 25, 20, 30, 25];
  const mockSparklineData2 = [2, 5, 3, 8, 12, 10, 15, 20, 18, 22];
  const mockSparklineData3 = [80, 85, 82, 88, 90, 85, 92, 95, 90, 94];
  const mockSparklineData4 = [10, 20, 30, 25, 40, 35, 50, 45, 60, 70];

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
      decimals: 0,
      prefix: "",
      suffix: "",
      icon: Zap,
      color: "text-violet-400",
      bgColor: "bg-violet-500/10",
      borderColor: "border-violet-500/20",
      trend: stats?.avg_efficiency_score ?? 0,
      trendLabel: "efficiency",
      sparklineData: mockSparklineData1,
      sparklineColor: "#a78bfa",
      leftBorder: "3px solid #3b82f6"
    },
    {
      id: "cost-saved",
      label: "Cost Saved",
      value: stats?.cost_saved_usd ?? 0,
      decimals: 4,
      prefix: "$",
      suffix: "",
      icon: DollarSign,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/20",
      trend: stats?.cost_saved_usd ?? 0,
      trendLabel: "saved",
      sparklineData: mockSparklineData2,
      sparklineColor: "#10b981",
      leftBorder: "3px solid #10b981"
    },
    {
      id: "cache-hit-rate",
      label: "Cache Hit Rate",
      value: stats?.cache_hit_rate ?? 0,
      decimals: 1,
      prefix: "",
      suffix: "%",
      icon: Target,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
      borderColor: "border-blue-500/20",
      trend: stats?.cache_hits ?? 0,
      trendLabel: "hits",
      sparklineData: mockSparklineData3,
      sparklineColor: "#3b82f6",
      leftBorder: "3px solid #06b6d4"
    },
    {
      id: "total-requests",
      label: "Requests",
      value: stats?.total_requests ?? 0,
      decimals: 0,
      prefix: "",
      suffix: "",
      icon: Activity,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      borderColor: "border-amber-500/20",
      trend: stats?.total_tokens_in ?? 0,
      trendLabel: "tokens in",
      sparklineData: mockSparklineData4,
      sparklineColor: "#fbbf24",
      leftBorder: "3px solid #a78bfa"
    },
  ];

  return (
    <section aria-label="Key metrics overview" className="animate-page-load">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              id={card.id}
              className={`relative overflow-hidden group hover:-translate-y-1`}
              style={{
                background: 'rgba(22,27,39,0.8)',
                backdropFilter: 'blur(10px)',
                WebkitBackdropFilter: 'blur(10px)',
                border: '1px solid rgba(59,130,246,0.15)',
                borderLeft: card.leftBorder,
                borderRadius: '12px',
                padding: '1.25rem',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease'
              }}
              role="status"
              aria-label={`${card.label}: ${card.value}`}
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
                <div className="flex flex-col items-end gap-1">
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
                  <div className="w-16 h-4 opacity-70 group-hover:opacity-100 transition-opacity">
                    <Sparklines data={card.sparklineData} margin={0}>
                      <SparklinesLine color={card.sparklineColor} style={{ strokeWidth: 2, fill: "none" }} />
                    </Sparklines>
                  </div>
                </div>
              </div>

              <p className="text-2xl font-bold tracking-tight">
                {loading ? "—" : (
                  <CountUp 
                    start={0} 
                    end={card.value} 
                    decimals={card.decimals} 
                    prefix={card.prefix} 
                    suffix={card.suffix} 
                    duration={1.5}
                    separator=","
                  />
                )}
              </p>
              <p className="text-sm text-muted-foreground mt-1">{card.label}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}
