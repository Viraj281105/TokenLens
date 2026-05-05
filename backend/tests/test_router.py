"""
TokenLens — Model Router Tests
================================
Tests for Layer 3: Complexity-Based Model Router.
"""

import pytest

from backend.core.model_router import ModelRouter, COST_PER_1K
from backend.models.schemas import ComplexityTier, ModelName


@pytest.fixture
def router() -> ModelRouter:
    """Create a fresh ModelRouter instance."""
    return ModelRouter()


class TestModelRouter:
    """Tests for the ModelRouter."""

    def test_simple_query_routes_to_flash(self, router: ModelRouter) -> None:
        """Short, simple queries should route to gemini-1.5-flash."""
        result = router.route("What is Python?", token_count=5)

        assert result.selected_model == ModelName.FLASH
        assert result.complexity_tier == ComplexityTier.SIMPLE

    def test_medium_query_routes_to_flash(self, router: ModelRouter) -> None:
        """Medium-length single-domain queries should route to flash."""
        prompt = "Explain the differences between lists and tuples in Python " * 3
        result = router.route(prompt, token_count=80)

        assert result.selected_model == ModelName.FLASH
        assert result.complexity_tier == ComplexityTier.MEDIUM

    def test_complex_query_routes_to_pro(self, router: ModelRouter) -> None:
        """Complex queries (code, math, multi-step) should route to pro."""
        code_prompt = """
        ```python
        def fibonacci(n):
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        ```
        Explain the time complexity of this function and optimize it.
        """
        result = router.route(code_prompt, token_count=50)

        assert result.selected_model == ModelName.PRO
        assert result.complexity_tier == ComplexityTier.COMPLEX

    def test_long_prompt_routes_to_pro(self, router: ModelRouter) -> None:
        """Prompts with 200+ tokens should route to pro regardless of content."""
        result = router.route("Simple question", token_count=250)

        assert result.selected_model == ModelName.PRO
        assert result.complexity_tier == ComplexityTier.COMPLEX

    def test_math_query_routes_to_pro(self, router: ModelRouter) -> None:
        """Math-heavy queries should route to pro."""
        math_prompt = "Calculate the integral of x^2 from 0 to 5."
        result = router.route(math_prompt, token_count=15)

        assert result.selected_model == ModelName.PRO
        assert result.complexity_tier == ComplexityTier.COMPLEX

    def test_cost_calculation_accuracy(self, router: ModelRouter) -> None:
        """Cost calculations should match the defined rate card."""
        result = router.route("Hello", token_count=100)

        # For flash model, 100 input tokens:
        # Input cost: (100/1000) * 0.000075 = 0.0000075
        # Output cost (est 150 tokens): (150/1000) * 0.0003 = 0.000045
        # Total: ~0.0000525
        assert result.estimated_cost_usd > 0
        assert result.estimated_cost_usd < 0.01  # Sanity bound

    def test_cost_savings_vs_pro(self, router: ModelRouter) -> None:
        """Flash routes should show savings compared to pro pricing."""
        result = router.route("What is 2+2?", token_count=10)

        if result.selected_model == ModelName.FLASH:
            assert result.cost_savings_vs_pro_usd > 0
        else:
            assert result.cost_savings_vs_pro_usd == 0.0

    def test_multistep_detected_as_complex(self, router: ModelRouter) -> None:
        """Multi-step reasoning prompts should be classified as complex."""
        prompt = "Compare and contrast React and Angular, listing pros and cons of each."
        result = router.route(prompt, token_count=30)

        assert result.complexity_tier == ComplexityTier.COMPLEX
