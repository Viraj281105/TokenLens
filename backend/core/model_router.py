"""
TokenLens — Layer 3: Complexity-Based Model Router
====================================================
Classifies prompt complexity and routes to the optimal Gemini model.
"""

from __future__ import annotations

import logging
import re
from typing import Final

from backend.models.schemas import ComplexityTier, ModelName, RoutingResult

logger = logging.getLogger("tokenlens.router")

COST_PER_1K: Final[dict[ModelName, dict[str, float]]] = {
    ModelName.FLASH: {"input": 0.000075, "output": 0.0003},
    ModelName.PRO: {"input": 0.00125, "output": 0.005},
}

CODE_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"```[\s\S]*?```"),
    re.compile(r"def\s+\w+\s*\("),
    re.compile(r"function\s+\w+\s*\("),
    re.compile(r"class\s+\w+"),
    re.compile(r"import\s+\w+"),
    re.compile(r"(for|while)\s*\("),
    re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE)\b", re.IGNORECASE),
]

MATH_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\b(calculate|compute|solve|equation|integral|derivative)\b", re.IGNORECASE),
    re.compile(r"\d+\s*[\+\-\*/\^]\s*\d+"),
    re.compile(r"\b(theorem|proof|lemma)\b", re.IGNORECASE),
]

MULTISTEP_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"\b(step[- ]by[- ]step|first.*then.*finally)\b", re.IGNORECASE),
    re.compile(r"\b(compare|contrast|analyze|evaluate|explain in detail)\b", re.IGNORECASE),
    re.compile(r"\b(write a|create a|build a|design a|implement)\b", re.IGNORECASE),
    re.compile(r"\b(pros and cons)\b", re.IGNORECASE),
]


class ModelRouter:
    """Routes prompts to the optimal Gemini model based on complexity."""

    def __init__(self) -> None:
        logger.info("ModelRouter initialized")

    def route(self, prompt: str, token_count: int) -> RoutingResult:
        tier = self._classify_complexity(prompt, token_count)
        model = self._select_model(tier)
        estimated_cost = self._estimate_cost(model, token_count)
        pro_cost = self._estimate_cost(ModelName.PRO, token_count)
        savings = max(0.0, pro_cost - estimated_cost)

        logger.info("Routed: tier=%s, model=%s, savings=$%.6f", tier.value, model.value, savings)

        return RoutingResult(
            selected_model=model,
            complexity_tier=tier,
            estimated_cost_usd=round(estimated_cost, 8),
            cost_savings_vs_pro_usd=round(savings, 8),
        )

    def _classify_complexity(self, prompt: str, token_count: int) -> ComplexityTier:
        has_code = any(p.search(prompt) for p in CODE_PATTERNS)
        has_math = any(p.search(prompt) for p in MATH_PATTERNS)
        has_multistep = any(p.search(prompt) for p in MULTISTEP_PATTERNS)
        is_complex = has_code or has_math or has_multistep

        if token_count > 200 or is_complex:
            return ComplexityTier.COMPLEX
        if token_count >= 50:
            return ComplexityTier.MEDIUM
        return ComplexityTier.SIMPLE

    @staticmethod
    def _select_model(tier: ComplexityTier) -> ModelName:
        if tier == ComplexityTier.COMPLEX:
            return ModelName.PRO
        return ModelName.FLASH

    @staticmethod
    def _estimate_cost(model: ModelName, input_tokens: int) -> float:
        costs = COST_PER_1K[model]
        estimated_output = int(input_tokens * 1.5)
        return (input_tokens / 1000) * costs["input"] + (estimated_output / 1000) * costs["output"]
