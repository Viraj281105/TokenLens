"""
TokenLens — Layer 4: Cost & Token Analytics Tracker
=====================================================
Tracks per-session and global metrics, persists to JSON on disk.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Final

from backend.models.schemas import HistoryEntry, StatsResponse

logger = logging.getLogger("tokenlens.tracker")

DEFAULT_LOG_PATH: Final[str] = "cost_log.json"
MAX_HISTORY: Final[int] = 1000


class CostTracker:
    """Thread-safe cost and token analytics tracker with JSON persistence."""

    def __init__(self, log_path: str = DEFAULT_LOG_PATH) -> None:
        self._lock = threading.RLock()
        self._log_path = Path(log_path)
        self._history: list[dict[str, Any]] = []

        # Aggregate counters
        self._total_requests: int = 0
        self._total_tokens_in: int = 0
        self._total_tokens_out: int = 0
        self._total_cost_usd: float = 0.0
        self._cost_saved_usd: float = 0.0
        self._cache_hits: int = 0
        self._compression_savings_tokens: int = 0
        self._total_efficiency: float = 0.0

        # Load existing data if available
        self._load()
        logger.info("CostTracker initialized, log_path=%s", self._log_path)

    def _load(self) -> None:
        """Load persisted history from disk."""
        if self._log_path.exists():
            try:
                with open(self._log_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._history = data.get("history", [])
                agg = data.get("aggregate", {})
                self._total_requests = agg.get("total_requests", 0)
                self._total_tokens_in = agg.get("total_tokens_in", 0)
                self._total_tokens_out = agg.get("total_tokens_out", 0)
                self._total_cost_usd = agg.get("total_cost_usd", 0.0)
                self._cost_saved_usd = agg.get("cost_saved_usd", 0.0)
                self._cache_hits = agg.get("cache_hits", 0)
                self._compression_savings_tokens = agg.get("compression_savings_tokens", 0)
                self._total_efficiency = agg.get("total_efficiency", 0.0)
                logger.info("Loaded %d history entries from disk", len(self._history))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load cost log: %s", e)

    def _save(self) -> None:
        """Persist current state to disk."""
        try:
            data = {
                "aggregate": {
                    "total_requests": self._total_requests,
                    "total_tokens_in": self._total_tokens_in,
                    "total_tokens_out": self._total_tokens_out,
                    "total_cost_usd": self._total_cost_usd,
                    "cost_saved_usd": self._cost_saved_usd,
                    "cache_hits": self._cache_hits,
                    "compression_savings_tokens": self._compression_savings_tokens,
                    "total_efficiency": self._total_efficiency,
                },
                "history": self._history[-MAX_HISTORY:],
            }
            with open(self._log_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except OSError as e:
            logger.error("Failed to save cost log: %s", e)

    def record_request(
        self,
        session_id: str,
        original_tokens: int,
        compressed_tokens: int,
        compression_ratio: float,
        cache_hit: bool,
        model_used: str,
        complexity_tier: str,
        estimated_cost: float,
        cost_saved: float,
        prompt_preview: str,
        output_tokens: int = 0,
    ) -> float:
        """
        Record a single request's metrics.

        Returns the efficiency_score for this request.
        """
        with self._lock:
            tokens_saved = original_tokens - compressed_tokens
            efficiency_score = (
                (tokens_saved / original_tokens * 100)
                if original_tokens > 0
                else 0.0
            )

            self._total_requests += 1
            self._total_tokens_in += original_tokens
            self._total_tokens_out += output_tokens
            self._total_cost_usd += estimated_cost
            self._cost_saved_usd += cost_saved
            self._compression_savings_tokens += tokens_saved
            self._total_efficiency += efficiency_score

            if cache_hit:
                self._cache_hits += 1

            entry = {
                "timestamp": time.time(),
                "session_id": session_id,
                "original_tokens": original_tokens,
                "compressed_tokens": compressed_tokens,
                "compression_ratio": round(compression_ratio, 4),
                "cache_hit": cache_hit,
                "model_used": model_used,
                "complexity_tier": complexity_tier,
                "estimated_cost": round(estimated_cost, 8),
                "cost_saved": round(cost_saved, 8),
                "efficiency_score": round(efficiency_score, 2),
                "prompt_preview": prompt_preview[:100],
            }
            self._history.append(entry)
            self._save()

            logger.info(
                "Recorded request: tokens=%d→%d, cost=$%.6f, saved=$%.6f, efficiency=%.1f%%",
                original_tokens, compressed_tokens, estimated_cost, cost_saved, efficiency_score,
            )
            return round(efficiency_score, 2)

    def get_summary(self) -> StatsResponse:
        """Get aggregate statistics."""
        with self._lock:
            cache_hit_rate = (
                (self._cache_hits / self._total_requests * 100)
                if self._total_requests > 0
                else 0.0
            )
            avg_efficiency = (
                (self._total_efficiency / self._total_requests)
                if self._total_requests > 0
                else 0.0
            )
            return StatsResponse(
                total_requests=self._total_requests,
                total_tokens_in=self._total_tokens_in,
                total_tokens_out=self._total_tokens_out,
                total_cost_usd=round(self._total_cost_usd, 6),
                cost_saved_usd=round(self._cost_saved_usd, 6),
                cache_hits=self._cache_hits,
                cache_hit_rate=round(cache_hit_rate, 2),
                compression_savings_tokens=self._compression_savings_tokens,
                avg_efficiency_score=round(avg_efficiency, 2),
            )

    def get_history(self, last_n: int = 20) -> list[dict[str, Any]]:
        """Return the last N request entries."""
        with self._lock:
            return self._history[-last_n:]

    def reset(self) -> None:
        """Reset all stats and history."""
        with self._lock:
            self._history.clear()
            self._total_requests = 0
            self._total_tokens_in = 0
            self._total_tokens_out = 0
            self._total_cost_usd = 0.0
            self._cost_saved_usd = 0.0
            self._cache_hits = 0
            self._compression_savings_tokens = 0
            self._total_efficiency = 0.0
            self._save()
            logger.info("CostTracker reset")
