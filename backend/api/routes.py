"""
TokenLens — API Routes
========================
All FastAPI endpoints: optimize, chat, stats, health, history.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends

from backend.api.middleware import verify_api_key
from backend.core.compressor import PromptCompressor
from backend.core.cost_tracker import CostTracker
from backend.core.gemini_client import GeminiClient
from backend.core.model_router import ModelRouter
from backend.core.monitoring import CloudMetricsEmitter
from backend.core.semantic_cache import SemanticCache
from backend.models.schemas import (
    HealthResponse,
    OptimizeRequest,
    OptimizeResponse,
    StatsResponse,
)

logger = logging.getLogger("tokenlens.routes")

router = APIRouter(prefix="/api", tags=["TokenLens API"])

# ── Singletons (initialized from main.py) ─────────────────────────────

compressor: PromptCompressor | None = None
cache: SemanticCache | None = None
model_router: ModelRouter | None = None
cost_tracker: CostTracker | None = None
gemini_client: GeminiClient | None = None
metrics_emitter: CloudMetricsEmitter | None = None


def init_components(
    _compressor: PromptCompressor,
    _cache: SemanticCache,
    _router: ModelRouter,
    _tracker: CostTracker,
    _gemini: GeminiClient,
    _metrics: CloudMetricsEmitter | None = None,
) -> None:
    """Initialize route-level references to core components."""
    global compressor, cache, model_router, cost_tracker, gemini_client, metrics_emitter
    compressor = _compressor
    cache = _cache
    model_router = _router
    cost_tracker = _tracker
    gemini_client = _gemini
    metrics_emitter = _metrics


# ── Endpoints ──────────────────────────────────────────────────────────

@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_prompt(
    request: OptimizeRequest,
    _api_key: str = Depends(verify_api_key),
) -> OptimizeResponse:
    """
    Run all 4 optimization layers on the input prompt.
    Returns full optimization report with LLM response.
    """
    assert compressor and cache and model_router and cost_tracker and gemini_client

    pipeline_start = time.perf_counter()

    # Layer 1: Compression
    compression = compressor.compress(request.prompt)

    # Layer 2: Semantic Cache lookup
    cache_result = cache.get(
        request.prompt,
        original_tokens=compression.original_tokens,
    )

    response_text: str
    output_tokens = 0

    if cache_result.cache_hit and cache_result.cached_response:
        response_text = cache_result.cached_response
        logger.info("Serving cached response for session=%s", request.session_id)
    else:
        # Layer 3: Model Routing
        routing = model_router.route(
            compression.compressed_prompt,
            compression.compressed_tokens,
        )

        # Generate response via Gemini
        try:
            response_text = await gemini_client.generate(
                compression.compressed_prompt,
                routing.selected_model.value,
            )
            output_tokens = compressor.count_tokens(response_text)
        except RuntimeError:
            response_text = (
                "[Gemini API not configured. Set GEMINI_API_KEY to enable LLM responses.]"
            )
        except Exception as e:
            logger.error("Generation failed: %s", str(e))
            response_text = f"[Generation error: {str(e)}]"

        # Store in cache
        cache.set(
            request.prompt,
            response_text,
            tokens_saved=compression.original_tokens - compression.compressed_tokens,
        )

    # Layer 3 results (compute even for cache hits for the response)
    routing = model_router.route(
        compression.compressed_prompt,
        compression.compressed_tokens,
    )

    # Layer 4: Record metrics
    efficiency_score = cost_tracker.record_request(
        session_id=request.session_id,
        original_tokens=compression.original_tokens,
        compressed_tokens=compression.compressed_tokens,
        compression_ratio=compression.compression_ratio,
        cache_hit=cache_result.cache_hit,
        model_used=routing.selected_model.value,
        complexity_tier=routing.complexity_tier.value,
        estimated_cost=routing.estimated_cost_usd,
        cost_saved=routing.cost_savings_vs_pro_usd,
        prompt_preview=request.prompt[:100],
        output_tokens=output_tokens,
    )

    # Emit Cloud Monitoring metrics
    if metrics_emitter:
        savings_ratio = 1.0 - compression.compression_ratio if compression.original_tokens > 0 else 0.0
        metrics_emitter.emit_token_savings(savings_ratio)
        cache_stats = cache.stats()
        metrics_emitter.emit_cache_hit_rate(cache_stats["hit_rate"])
        metrics_emitter.emit_cost_per_request(routing.estimated_cost_usd)

    pipeline_ms = (time.perf_counter() - pipeline_start) * 1000

    return OptimizeResponse(
        original_tokens=compression.original_tokens,
        compressed_tokens=compression.compressed_tokens,
        compression_ratio=compression.compression_ratio,
        compressed_prompt=compression.compressed_prompt,
        cache_hit=cache_result.cache_hit,
        similarity_score=cache_result.similarity_score,
        model_used=routing.selected_model,
        complexity_tier=routing.complexity_tier,
        estimated_cost=routing.estimated_cost_usd,
        cost_saved=routing.cost_savings_vs_pro_usd,
        response_text=response_text,
        efficiency_score=efficiency_score,
        optimization_pipeline_ms=round(pipeline_ms, 2),
        session_id=request.session_id,
    )


@router.post("/chat", response_model=OptimizeResponse)
async def chat(
    request: OptimizeRequest,
    _api_key: str = Depends(verify_api_key),
) -> OptimizeResponse:
    """Alias for /optimize — optimized chat completion."""
    return await optimize_prompt(request, _api_key)


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    _api_key: str = Depends(verify_api_key),
) -> StatsResponse:
    """Return global cost + token statistics."""
    assert cost_tracker
    return cost_tracker.get_summary()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint (no auth required)."""
    components: dict[str, str] = {}
    components["compressor"] = "ok" if compressor else "not initialized"
    components["cache"] = "ok" if cache else "not initialized"
    components["router"] = "ok" if model_router else "not initialized"
    components["tracker"] = "ok" if cost_tracker else "not initialized"
    components["gemini"] = (
        "ok" if gemini_client and gemini_client.is_configured else "not configured"
    )

    return HealthResponse(components=components)


@router.get("/history")
async def get_history(
    last_n: int = 20,
    _api_key: str = Depends(verify_api_key),
) -> list[dict[str, Any]]:
    """Return the last N optimization requests with details."""
    assert cost_tracker
    return cost_tracker.get_history(min(last_n, 100))
