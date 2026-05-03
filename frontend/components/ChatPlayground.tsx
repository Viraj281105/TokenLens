"use client";

import { useState, useRef } from "react";
import {
  Send,
  Loader2,
  Sparkles,
  ArrowRight,
  Copy,
  Check,
} from "lucide-react";

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

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

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
          "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
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

  return (
    <section
      aria-label="Chat playground"
      className="glass-card p-6 animate-fade-in"
    >
      <div className="flex items-center gap-3 mb-5">
        <div className="p-2 rounded-xl bg-violet-500/10 border border-violet-500/20">
          <Sparkles className="w-5 h-5 text-violet-400" aria-hidden="true" />
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
            className="text-xs px-3 py-1.5 rounded-full border border-zinc-700 text-zinc-400 hover:border-violet-500/50 hover:text-violet-300 transition-all focus-ring"
            aria-label={`Use example: ${ex.substring(0, 40)}...`}
          >
            {ex.substring(0, 45)}…
          </button>
        ))}
      </div>

      {/* Input area */}
      <div className="relative mb-4">
        <label htmlFor="prompt-input" className="sr-only">
          Enter your prompt
        </label>
        <textarea
          ref={textareaRef}
          id="prompt-input"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              handleOptimize();
            }
          }}
          placeholder="Enter your prompt here... (Ctrl+Enter to send)"
          className="w-full bg-zinc-900/80 border border-zinc-700 rounded-xl px-4 py-3 text-sm text-foreground placeholder:text-zinc-500 resize-none focus-ring transition-colors focus:border-violet-500/50"
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
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-medium text-white transition-all focus-ring"
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

      {/* Error */}
      {error && (
        <div
          role="alert"
          className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm"
        >
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4 animate-slide-up">
          {/* Pipeline stats bar */}
          <div className="flex flex-wrap items-center gap-3 p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 text-xs text-zinc-400">
            <span className={tierBadgeClass(result.complexity_tier)}>
              {result.complexity_tier}
            </span>
            <span>
              Model: <strong className="text-foreground">{result.model_used}</strong>
            </span>
            <span>
              Pipeline:{" "}
              <strong className="text-foreground">
                {result.optimization_pipeline_ms.toFixed(0)}ms
              </strong>
            </span>
            {result.cache_hit && (
              <span className="badge badge-simple">⚡ Cache Hit</span>
            )}
            <span>
              Efficiency:{" "}
              <strong className="text-emerald-400">
                {result.efficiency_score.toFixed(1)}%
              </strong>
            </span>
          </div>

          {/* Side-by-side comparison */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Original */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-zinc-400">
                  Original Prompt
                </h3>
                <span className="text-xs text-zinc-500">
                  {result.original_tokens} tokens
                </span>
              </div>
              <div className="p-3 rounded-lg bg-zinc-900/80 border border-zinc-800 text-sm leading-relaxed max-h-48 overflow-auto font-mono">
                {prompt}
              </div>
            </div>

            {/* Compressed */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-violet-400 flex items-center gap-1">
                  <ArrowRight className="w-3 h-3" aria-hidden="true" />
                  Compressed
                </h3>
                <span className="text-xs text-emerald-400 font-semibold">
                  {result.compressed_tokens} tokens (
                  {((1 - result.compression_ratio) * 100).toFixed(0)}% saved)
                </span>
              </div>
              <div className="p-3 rounded-lg bg-violet-950/30 border border-violet-500/20 text-sm leading-relaxed max-h-48 overflow-auto font-mono">
                {result.compressed_prompt}
              </div>
            </div>
          </div>

          {/* Cost breakdown */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              {
                label: "Est. Cost",
                value: `$${result.estimated_cost.toFixed(6)}`,
                color: "text-zinc-300",
              },
              {
                label: "Cost Saved",
                value: `$${result.cost_saved.toFixed(6)}`,
                color: "text-emerald-400",
              },
              {
                label: "Compression",
                value: `${(result.compression_ratio * 100).toFixed(0)}%`,
                color: "text-violet-400",
              },
              {
                label: "Similarity",
                value: result.similarity_score
                  ? `${(result.similarity_score * 100).toFixed(1)}%`
                  : "N/A",
                color: "text-blue-400",
              },
            ].map((item) => (
              <div
                key={item.label}
                className="p-3 rounded-lg bg-zinc-900/50 border border-zinc-800 text-center"
              >
                <p className={`text-lg font-bold ${item.color}`}>
                  {item.value}
                </p>
                <p className="text-xs text-zinc-500 mt-0.5">{item.label}</p>
              </div>
            ))}
          </div>

          {/* Response */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-medium text-zinc-400">
                LLM Response
              </h3>
              <button
                onClick={() => handleCopy(result.response_text)}
                className="flex items-center gap-1 text-xs text-zinc-500 hover:text-violet-400 transition-colors focus-ring p-1 rounded"
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
            <div className="p-4 rounded-lg bg-zinc-900/80 border border-zinc-800 text-sm leading-relaxed max-h-64 overflow-auto whitespace-pre-wrap">
              {result.response_text}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
