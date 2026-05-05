"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import { BarChart3 } from "lucide-react";

interface HistoryEntry {
  timestamp: number;
  original_tokens: number;
  compressed_tokens: number;
  compression_ratio: number;
  cache_hit: boolean;
  model_used: string;
  complexity_tier: string;
  estimated_cost: number;
  cost_saved: number;
  efficiency_score: number;
  prompt_preview: string;
}

const API_BASE = "";

export default function CostChart() {
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/history?last_n=20`, {
          headers: {
            "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || 'tokenlens2026',
          },
        });
        if (res.ok) {
          setHistory(await res.json());
        }
      } catch {
        // Silently fail
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
    const interval = setInterval(fetchHistory, 5000);
    return () => clearInterval(interval);
  }, []);

  const chartData = history.map((entry, idx) => ({
    name: `#${idx + 1}`,
    costSaved: Number((entry.cost_saved * 1000).toFixed(4)),
    efficiency: entry.efficiency_score,
    tokens: entry.original_tokens - entry.compressed_tokens,
  }));

  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) => {
    if (!active || !payload) return null;
    return (
      <div className="bg-zinc-900 border border-zinc-700 rounded-lg p-3 shadow-xl text-xs">
        <p className="text-zinc-400 mb-2 font-medium">{label}</p>
        {payload.map((entry, i) => (
          <div key={i} className="flex items-center gap-2 mb-1">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-zinc-400">{entry.name}:</span>
            <span className="text-foreground font-medium">{entry.value}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <section
      aria-label="Cost savings chart"
      className="glass-card p-6 animate-fade-in"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
          <BarChart3
            className="w-5 h-5 text-emerald-400"
            aria-hidden="true"
          />
        </div>
        <div>
          <h2 className="text-lg font-semibold">Cost Savings Over Time</h2>
          <p className="text-sm text-muted-foreground">
            Last 20 requests — cost saved per request (×10⁻³ USD)
          </p>
        </div>
      </div>

      {loading ? (
        <div
          className="h-64 flex items-center justify-center text-zinc-500"
          role="status"
          aria-label="Loading chart data"
        >
          <div className="animate-shimmer w-full h-full rounded-lg" />
        </div>
      ) : chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-zinc-500">
          <p>No data yet. Send a prompt to see optimization trends.</p>
        </div>
      ) : (
        <div className="h-72" role="img" aria-label="Line chart showing cost savings over the last 20 requests">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 8, right: 8, left: -16, bottom: 0 }}
            >
              <defs>
                <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a78bfa" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#a78bfa" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="effGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="rgba(63,63,70,0.3)"
                vertical={false}
              />
              <XAxis
                dataKey="name"
                stroke="#52525b"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#52525b"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="costSaved"
                name="Cost Saved (×10⁻³)"
                stroke="#a78bfa"
                strokeWidth={2}
                fill="url(#costGrad)"
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2 }}
              />
              <Area
                type="monotone"
                dataKey="efficiency"
                name="Efficiency %"
                stroke="#22c55e"
                strokeWidth={2}
                fill="url(#effGrad)"
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
