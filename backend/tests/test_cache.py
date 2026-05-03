"""
TokenLens — Semantic Cache Tests
==================================
Tests for Layer 2: FAISS Semantic Cache.
"""

import pytest

from backend.core.semantic_cache import SemanticCache, MAX_CACHE_SIZE


@pytest.fixture
def cache() -> SemanticCache:
    """Create a fresh SemanticCache instance."""
    c = SemanticCache()
    c.clear()
    return c


class TestSemanticCache:
    """Tests for the SemanticCache."""

    def test_cache_hit_on_similar_prompt(self, cache: SemanticCache) -> None:
        """Semantically similar prompts should produce cache hits."""
        prompt1 = "What is the capital of France?"
        response1 = "The capital of France is Paris."

        cache.set(prompt1, response1, tokens_saved=10)

        # Very similar prompt
        prompt2 = "What's the capital city of France?"
        result = cache.get(prompt2, original_tokens=8)

        assert result.cache_hit is True
        assert result.cached_response == response1
        assert result.similarity_score is not None
        assert result.similarity_score >= 0.92

    def test_cache_miss_on_different_prompt(self, cache: SemanticCache) -> None:
        """Semantically different prompts should produce cache misses."""
        cache.set(
            "What is the capital of France?",
            "The capital of France is Paris.",
            tokens_saved=10,
        )

        # Completely different topic
        result = cache.get("How do you implement a binary search tree in Python?")

        assert result.cache_hit is False

    def test_cache_lru_eviction(self, cache: SemanticCache) -> None:
        """Cache should evict LRU entries when exceeding max size."""
        # We won't actually insert 1000+ entries in a unit test (too slow),
        # but we can test the eviction mechanism with a smaller scale
        # by temporarily patching MAX_CACHE_SIZE
        import backend.core.semantic_cache as cache_module

        original_max = cache_module.MAX_CACHE_SIZE
        cache_module.MAX_CACHE_SIZE = 3

        try:
            small_cache = SemanticCache()
            small_cache.clear()

            # Insert 4 entries (should evict the first one)
            for i in range(4):
                small_cache.set(
                    f"Unique prompt number {i} about topic {i * 100}",
                    f"Response {i}",
                    tokens_saved=5,
                )

            stats = small_cache.stats()
            assert stats["cache_size"] <= 3
        finally:
            cache_module.MAX_CACHE_SIZE = original_max

    def test_stats_accuracy(self, cache: SemanticCache) -> None:
        """Stats should accurately reflect cache operations."""
        cache.set("Test prompt about weather", "It's sunny.", tokens_saved=5)
        cache.get("Test prompt about weather conditions", original_tokens=6)
        cache.get("Completely unrelated quantum physics question", original_tokens=10)

        stats = cache.stats()

        assert stats["total_queries"] == 2
        assert stats["cache_size"] == 1
        assert isinstance(stats["hit_rate"], float)
        assert isinstance(stats["tokens_saved_via_cache"], int)

    def test_cache_clear(self, cache: SemanticCache) -> None:
        """Clearing the cache should reset all state."""
        cache.set("Test prompt", "Test response", tokens_saved=5)
        cache.clear()

        stats = cache.stats()
        assert stats["cache_size"] == 0
        assert stats["total_queries"] == 0
        assert stats["total_hits"] == 0

    def test_duplicate_prompt_not_duplicated(self, cache: SemanticCache) -> None:
        """Setting the same prompt twice should not create duplicates."""
        cache.set("What is Python?", "Python is a language.", tokens_saved=5)
        cache.set("What is Python?", "Python is a language.", tokens_saved=5)

        stats = cache.stats()
        assert stats["cache_size"] == 1
