"""
TokenLens — Pydantic v2 Data Models
====================================
Defines all request/response schemas for the API with strict validation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ── Enums ──────────────────────────────────────────────────────────────

class ComplexityTier(str, Enum):
    """Model complexity classification tiers."""
    SIMPLE = "SIMPLE"
    MEDIUM = "MEDIUM"
    COMPLEX = "COMPLEX"


class ModelName(str, Enum):
    """Supported Gemini model identifiers."""
    FLASH = "gemini-1.5-flash"
    PRO = "gemini-1.5-pro"


# ── Request Schemas ────────────────────────────────────────────────────

class OptimizeRequest(BaseModel):
    """Request body for /api/optimize and /api/chat."""
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="The prompt text to optimize and send to the LLM.",
    )
    session_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique session identifier for tracking.",
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response.",
    )

    @field_validator("prompt")
    @classmethod
    def sanitize_prompt(cls, v: str) -> str:
        """Strip leading/trailing whitespace and reject dangerous patterns."""
        v = v.strip()
        dangerous_patterns = [
            "<script",
            "javascript:",
            "data:text/html",
            "onclick=",
            "onerror=",
        ]
        lower_v = v.lower()
        for pattern in dangerous_patterns:
            if pattern in lower_v:
                raise ValueError(f"Input contains disallowed pattern: {pattern}")
        return v


# ── Response Schemas ───────────────────────────────────────────────────

class CompressionResult(BaseModel):
    """Output from Layer 1 — Prompt Compression."""
    compressed_prompt: str
    original_tokens: int = Field(ge=0)
    compressed_tokens: int = Field(ge=0)
    compression_ratio: float = Field(
        ge=0.0, le=1.0,
        description="Fraction of tokens retained (compressed / original).",
    )


class CacheResult(BaseModel):
    """Output from Layer 2 — Semantic Cache."""
    cache_hit: bool
    cached_response: Optional[str] = None
    similarity_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    tokens_saved: int = Field(default=0, ge=0)


class RoutingResult(BaseModel):
    """Output from Layer 3 — Model Router."""
    selected_model: ModelName
    complexity_tier: ComplexityTier
    estimated_cost_usd: float = Field(ge=0.0)
    cost_savings_vs_pro_usd: float = Field(ge=0.0)


class OptimizeResponse(BaseModel):
    """Full response from /api/optimize combining all layers."""
    # Layer 1: Compression
    original_tokens: int = Field(ge=0)
    compressed_tokens: int = Field(ge=0)
    compression_ratio: float = Field(ge=0.0, le=1.0)
    compressed_prompt: str

    # Layer 2: Cache
    cache_hit: bool
    similarity_score: Optional[float] = None

    # Layer 3: Routing
    model_used: ModelName
    complexity_tier: ComplexityTier
    estimated_cost: float = Field(ge=0.0)
    cost_saved: float = Field(ge=0.0)

    # LLM output
    response_text: str

    # Layer 4: Analytics
    efficiency_score: float = Field(ge=0.0, le=100.0)
    optimization_pipeline_ms: float = Field(ge=0.0)

    # Metadata
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatsResponse(BaseModel):
    """Global statistics from /api/stats."""
    total_requests: int = Field(default=0, ge=0)
    total_tokens_in: int = Field(default=0, ge=0)
    total_tokens_out: int = Field(default=0, ge=0)
    total_cost_usd: float = Field(default=0.0, ge=0.0)
    cost_saved_usd: float = Field(default=0.0, ge=0.0)
    cache_hits: int = Field(default=0, ge=0)
    cache_hit_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    compression_savings_tokens: int = Field(default=0, ge=0)
    avg_efficiency_score: float = Field(default=0.0, ge=0.0, le=100.0)


class HistoryEntry(BaseModel):
    """Single entry in request history."""
    timestamp: datetime
    session_id: str
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float
    cache_hit: bool
    model_used: ModelName
    complexity_tier: ComplexityTier
    estimated_cost: float
    cost_saved: float
    efficiency_score: float
    prompt_preview: str = Field(
        description="First 100 characters of the original prompt.",
    )


class HealthResponse(BaseModel):
    """Response from /api/health."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: dict[str, str] = Field(
        default_factory=lambda: {
            "compressor": "ok",
            "cache": "ok",
            "router": "ok",
            "tracker": "ok",
        }
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
