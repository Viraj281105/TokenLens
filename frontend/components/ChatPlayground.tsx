"use client";

import { useState, useRef } from "react";
import {
  Send,
  Loader2,
  Sparkles,
  ArrowRight,
  Copy,
  Check,
  Zap,
  BarChart3,
  Percent,
  Clock,
  Cpu
} from "lucide-react";
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface OptimizeResult {
  original_tokens: number;
  compressed_tokens: number;
  compression_ratio: number;
  compressed_prompt: string;
  cache_hit: boolean;
  similarity_score: number | null;
  model_used: string;
  complexity_tier: string;
  estimated_cost: number;
  cost_saved: number;
  response_text: string;
  efficiency_score: number;
  optimization_pipeline_ms: number;
  session_id: string;
}

const API_BASE = "";

const EXAMPLE_PROMPTS = [
  "What is machine learning? Explain the basic concepts and how it differs from traditional programming. I would like to understand the fundamentals thoroughly.",
  "Write a Python function to calculate the Fibonacci sequence using dynamic programming with memoization.",
  "Compare and contrast REST and GraphQL APIs, listing pros and cons of each approach for modern web development.",
  "What is the capital of France?",
];

export default function ChatPlayground() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState<OptimizeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleOptimize = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/optimize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || 'tokenlens2026',
        },
        body: JSON.stringify({ prompt: prompt.trim() }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${res.status}`);
      }

      setResult(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tierBadgeClass = (tier: string) => {
    switch (tier) {
      case "SIMPLE": return "badge badge-simple";
      case "MEDIUM": return "badge badge-medium";
      case "COMPLEX": return "badge badge-complex";
      default: return "badge";
    }
  };

  // Custom syntax highlighter style to simulate diff
  const customStyle = {
    ...vscDarkPlus,
    'pre[class*="language-"]': {
      ...vscDarkPlus['pre[class*="language-"]'],
      background: 'transparent',
      margin: 0,
      padding: 0,
    }
  };

  return (
    <section
      aria-label="Chat playground"
      className="glass-card p-6 animate-page-load"
      style={{ animationDelay: '0.3s' }}
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2 rounded-xl bg-purple-500/10 border border-purple-500/20">
          <Sparkles className="w-5 h-5 text-purple-400" aria-hidden="true" />
        </div>
        <div>
          <h2 className="text-lg font-semibold">Optimization Playground</h2>
          <p className="text-sm text-muted-foreground">
            Enter a prompt to see the full optimization pipeline in action
          </p>
        </div>
      </div>

      {/* Example prompts */}
      <div className="flex flex-wrap gap-2 mb-4" role="group" aria-label="Example prompts">
        {EXAMPLE_PROMPTS.map((ex, i) => (
          <button
            key={i}
            id={`example-prompt-${i}`}
            onClick={() => {
              setPrompt(ex);
              textareaRef.current?.focus();
            }}
            className="text-xs px-3 py-1.5 rounded-full border border-blue-500/20 bg-blue-500/5 text-zinc-400 hover:border-blue-500/50 hover:bg-blue-500/10 hover:text-blue-300 transition-all focus-ring"
            aria-label={`Use example: ${ex.substring(0, 40)}...`}
          >
            {ex.substring(0, 45)}…
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Pane: Input area */}
        <div className="relative flex flex-col">
          <label htmlFor="prompt-input" className="sr-only">
            Enter your prompt
          </label>
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              id="prompt-input"
              rows={6}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  handleOptimize();
                }
              }}
              placeholder="Enter your prompt here... (Ctrl+Enter to send)"
              className="w-full h-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-zinc-600 resize-none focus-ring transition-colors focus:border-blue-500/50"
              maxLength={10000}
              aria-describedby="char-count"
            />
            <div className="absolute bottom-3 right-3 flex items-center gap-3">
              <span
                id="char-count"
                className="text-xs text-zinc-500"
                aria-live="polite"
              >
                {prompt.length}/10,000
              </span>
              <button
                id="optimize-button"
                onClick={handleOptimize}
                disabled={!prompt.trim() || loading}
                className="flex items-center gap-2 px-4 py-2 disabled:opacity-40 disabled:cursor-not-allowed text-sm transition-all focus-ring shadow-lg shadow-blue-500/20"
                style={{
                  background: 'linear-gradient(to right, #3b82f6, #a78bfa)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  padding: '8px 20px',
                  cursor: 'pointer',
                  fontWeight: '600'
                }}
                aria-label="Optimize prompt"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                ) : (
                  <Send className="w-4 h-4" aria-hidden="true" />
                )}
                {loading ? "Optimizing…" : "Optimize"}
              </button>
            </div>
          </div>
          
          {loading && (
            <div className="mt-4 h-1.5 w-full bg-zinc-900 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 w-full animate-shimmer" />
            </div>
          )}
          
          {/* Error */}
          {error && (
            <div
              role="alert"
              className="mt-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm"
            >
              {error}
            </div>
          )}
        </div>

        {/* Right Pane: Results Output */}
        <div className="flex flex-col h-full min-h-[250px]">
          {!result && !loading && (
            <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-zinc-800 rounded-xl bg-zinc-950/30 text-zinc-600 p-6 text-center">
              <Sparkles className="w-8 h-8 mb-3 opacity-20" />
              <p>Output will appear here after optimization.</p>
            </div>
          )}
          
          {loading && !result && (
             <div className="flex-1 flex items-center justify-center border border-zinc-800 rounded-xl bg-zinc-950/30">
               <div className="flex flex-col items-center gap-3">
                 <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />
                 <span className="text-sm text-zinc-400 animate-pulse">Running optimization pipeline...</span>
               </div>
             </div>
          )}

          {result && (
            <div className="space-y-4 animate-slide-up flex-1">
              {/* Compressed Output */}
              <div className="space-y-2 h-full flex flex-col">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-blue-400 flex items-center gap-1">
                    <ArrowRight className="w-3 h-3" aria-hidden="true" />
                    Compressed Prompt
                  </h3>
                  <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {((1 - result.compression_ratio) * 100).toFixed(0)}% saved
                  </span>
                </div>
                <div className="p-3 rounded-lg bg-zinc-950 border border-blue-500/20 text-sm leading-relaxed max-h-[160px] overflow-auto flex-1">
                  <SyntaxHighlighter
                    language="text"
                    style={customStyle}
                    wrapLines={true}
                    lineProps={(lineNumber) => {
                       // Very basic heuristic for highlighting: if it's shorter, some things are removed.
                       // In a real app we'd get diff tokens from backend.
                       return { style: { display: "block", color: "#34d399" } };
                    }}
                  >
                    {result.compressed_prompt}
                  </SyntaxHighlighter>
                </div>
              </div>

              {/* Pipeline stats bar */}
              <div className="flex flex-wrap items-center gap-2 p-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800 text-xs text-zinc-400">
                <span className={tierBadgeClass(result.complexity_tier)}>
                  {result.complexity_tier}
                </span>
                <span className="flex items-center gap-1">
                  <Cpu className="w-3 h-3" /> {result.model_used}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {result.optimization_pipeline_ms.toFixed(0)}ms
                </span>
                {result.cache_hit && (
                  <span className="badge badge-simple ml-auto">⚡ Cache Hit</span>
                )}
              </div>

              {/* Cost breakdown */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  {
                    label: "Est. Cost",
                    value: `$${result.estimated_cost.toFixed(6)}`,
                    color: "text-zinc-300",
                    icon: <BarChart3 className="w-3 h-3 opacity-50" />
                  },
                  {
                    label: "Cost Saved",
                    value: `$${result.cost_saved.toFixed(6)}`,
                    color: "text-emerald-400",
                    icon: <Zap className="w-3 h-3 opacity-50 text-emerald-400" />
                  },
                  {
                    label: "Compression",
                    value: `${(result.compression_ratio * 100).toFixed(0)}%`,
                    color: "text-purple-400",
                    icon: <Percent className="w-3 h-3 opacity-50 text-purple-400" />
                  },
                  {
                    label: "Similarity",
                    value: result.similarity_score
                      ? `${(result.similarity_score * 100).toFixed(1)}%`
                      : "N/A",
                    color: "text-blue-400",
                    icon: <Sparkles className="w-3 h-3 opacity-50 text-blue-400" />
                  },
                ].map((item) => (
                  <div
                    key={item.label}
                    className="p-3 rounded-lg glass-card border border-zinc-800 hover:border-blue-500/30 text-center transition-colors flex flex-col items-center justify-center"
                  >
                    <div className="flex items-center gap-1 mb-1">
                      {item.icon}
                      <p className="text-[10px] text-zinc-500 uppercase tracking-wider">{item.label}</p>
                    </div>
                    <p className={`text-sm font-bold ${item.color}`}>
                      {item.value}
                    </p>
                  </div>
                ))}
              </div>

              {/* Response */}
              <div className="space-y-2 mt-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-medium text-zinc-400">
                    LLM Response
                  </h3>
                  <button
                    onClick={() => handleCopy(result.response_text)}
                    className="flex items-center gap-1 text-xs text-zinc-500 hover:text-blue-400 transition-colors focus-ring p-1 rounded bg-zinc-900 border border-zinc-800 hover:border-blue-500/30"
                    aria-label="Copy response to clipboard"
                  >
                    {copied ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <div className="p-4 rounded-lg bg-zinc-950/80 border border-zinc-800 text-sm leading-relaxed max-h-[200px] overflow-auto text-zinc-300 font-sans shadow-inner">
                  {result.response_text}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
