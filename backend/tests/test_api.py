"""
TokenLens — API Integration Tests
====================================
Tests for FastAPI endpoints using httpx AsyncClient.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.api.routes import init_components
from backend.core.compressor import PromptCompressor
from backend.core.semantic_cache import SemanticCache  
from backend.core.model_router import ModelRouter
from backend.core.cost_tracker import CostTracker
from backend.core.gemini_client import GeminiClient


# Set test env vars before importing the app
os.environ["TOKEN_LENS_API_KEY"] = "test-api-key-12345"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest_asyncio.fixture
async def client():
    """Create an async test client with mocked heavy dependencies."""
    # Mock sentence-transformers to avoid loading the model in tests
    mock_model = MagicMock()
    mock_model.encode.return_value = __import__("numpy").random.randn(384).astype("float32")

    with patch("backend.core.semantic_cache.SentenceTransformer", return_value=mock_model):
        from backend.main import app
        
        # Initialize the global components before tests run
        init_components(
            compressor=PromptCompressor(),
            cache=SemanticCache(),
            model_router=ModelRouter(),
            cost_tracker=CostTracker(),
            gemini_client=GeminiClient()
        )
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


class TestAPI:
    """Integration tests for the TokenLens API."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client: AsyncClient) -> None:
        """Health endpoint should return 200 without auth."""
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data
        assert "version" in data

    @pytest.mark.asyncio
    async def test_optimize_endpoint_returns_all_fields(self, client: AsyncClient) -> None:
        """Optimize endpoint should return all expected fields."""
        with patch("backend.api.routes.gemini_client") as mock_gemini:
            mock_gemini.is_configured = True
            mock_gemini.generate = AsyncMock(return_value="This is a test response.")

            response = await client.post(
                "/api/optimize",
                json={
                    "prompt": "What is machine learning? Explain the basic concepts.",
                    "session_id": "test-session-001",
                },
                headers={"X-API-Key": "test-api-key-12345"},
            )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields are present
        required_fields = [
            "original_tokens",
            "compressed_tokens",
            "compression_ratio",
            "compressed_prompt",
            "cache_hit",
            "model_used",
            "complexity_tier",
            "estimated_cost",
            "cost_saved",
            "response_text",
            "efficiency_score",
            "optimization_pipeline_ms",
            "session_id",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        assert data["original_tokens"] > 0
        assert data["compression_ratio"] <= 1.0
        assert data["optimization_pipeline_ms"] > 0

    @pytest.mark.asyncio
    async def test_invalid_api_key_rejected(self, client: AsyncClient) -> None:
        """Requests with invalid API keys should be rejected."""
        response = await client.post(
            "/api/optimize",
            json={"prompt": "Test prompt"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_api_key_rejected(self, client: AsyncClient) -> None:
        """Requests without API key should be rejected."""
        response = await client.post(
            "/api/optimize",
            json={"prompt": "Test prompt"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_stats_endpoint(self, client: AsyncClient) -> None:
        """Stats endpoint should return valid statistics."""
        response = await client.get(
            "/api/stats",
            headers={"X-API-Key": "test-api-key-12345"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "total_cost_usd" in data
        assert "cache_hit_rate" in data

    @pytest.mark.asyncio
    async def test_history_endpoint(self, client: AsyncClient) -> None:
        """History endpoint should return a list."""
        response = await client.get(
            "/api/history",
            headers={"X-API-Key": "test-api-key-12345"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_prompt_too_long_rejected(self, client: AsyncClient) -> None:
        """Prompts exceeding 10000 chars should be rejected."""
        response = await client.post(
            "/api/optimize",
            json={"prompt": "x" * 10001},
            headers={"X-API-Key": "test-api-key-12345"},
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_dangerous_input_rejected(self, client: AsyncClient) -> None:
        """Prompts with XSS patterns should be rejected."""
        response = await client.post(
            "/api/optimize",
            json={"prompt": "<script>alert('xss')</script>"},
            headers={"X-API-Key": "test-api-key-12345"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_prompt_rejected(self, client: AsyncClient) -> None:
        """Empty prompts should be rejected."""
        response = await client.post(
            "/api/optimize",
            json={"prompt": ""},
            headers={"X-API-Key": "test-api-key-12345"},
        )
        assert response.status_code == 422
