"""
TokenLens — Compressor Tests
==============================
Tests for Layer 1: Prompt Compression Engine.
"""

import pytest

from backend.core.compressor import PromptCompressor


@pytest.fixture
def compressor() -> PromptCompressor:
    """Create a fresh PromptCompressor instance."""
    return PromptCompressor()


class TestCompression:
    """Tests for the PromptCompressor."""

    def test_compression_reduces_tokens(self, compressor: PromptCompressor) -> None:
        """Verify that compression actually reduces token count on verbose input."""
        verbose_prompt = (
            "I was wondering if you could please help me understand something. "
            "Basically, I would like to know how machine learning works. "
            "In other words, I want to understand the fundamentals of ML. "
            "It is important to note that I am a beginner in this field. "
            "To be honest, I have no prior experience with data science. "
            "Could you please explain the basic concepts of machine learning? "
            "Needless to say, I would appreciate a simple and clear explanation. "
            "As a matter of fact, I have tried reading some books but they were too complex. "
            "All things considered, I think a step-by-step approach would be best. "
            "At the end of the day, I just want to learn the basics effectively."
        )
        result = compressor.compress(verbose_prompt)

        assert result.compressed_tokens < result.original_tokens
        assert result.compression_ratio < 1.0
        assert len(result.compressed_prompt) > 0

    def test_compression_preserves_meaning(self, compressor: PromptCompressor) -> None:
        """Verify that key content words survive compression."""
        prompt = (
            "Please explain the concept of neural networks in deep learning. "
            "I would like to understand how backpropagation works. "
            "It is worth noting that gradient descent is a key optimization method. "
            "Could you please describe the role of activation functions? "
            "Basically, I want a comprehensive overview of deep learning fundamentals."
        )
        result = compressor.compress(prompt)

        compressed_lower = result.compressed_prompt.lower()
        # Core concepts must survive compression
        assert "neural" in compressed_lower or "network" in compressed_lower
        assert "learning" in compressed_lower
        assert "backpropagation" in compressed_lower or "gradient" in compressed_lower

    def test_compression_never_below_60_percent(self, compressor: PromptCompressor) -> None:
        """Verify the 60% minimum retention floor is enforced."""
        prompt = (
            "Basically, I really just want to know something simple. "
            "To be honest, it's actually a very straightforward question. "
            "Essentially, I would like you to tell me what Python is. "
            "In my opinion, Python is sort of a good programming language. "
            "You know, it is kind of easy to learn, as you can see. "
            "Needless to say, I was wondering if you could help me. "
            "As I mentioned before, please note that I am a beginner. "
            "For what it's worth, I think programming is interesting."
        )
        result = compressor.compress(prompt)

        # Compression ratio should be >= 0.60 (at least 60% retained)
        assert result.compression_ratio >= 0.60, (
            f"Compression ratio {result.compression_ratio} is below the 0.60 minimum"
        )

    def test_short_prompt_not_compressed(self, compressor: PromptCompressor) -> None:
        """Very short prompts should not be compressed."""
        prompt = "What is Python?"
        result = compressor.compress(prompt)

        assert result.compression_ratio == 1.0
        assert result.compressed_prompt == prompt
        assert result.original_tokens == result.compressed_tokens

    def test_token_counting_accuracy(self, compressor: PromptCompressor) -> None:
        """Verify token counting returns reasonable values."""
        text = "Hello, world!"
        tokens = compressor.count_tokens(text)
        assert tokens > 0
        assert isinstance(tokens, int)

    def test_whitespace_normalization(self, compressor: PromptCompressor) -> None:
        """Verify excessive whitespace is collapsed."""
        prompt = (
            "This   has    lots     of      spaces.\n\n\n\n\n"
            "And   too   many   newlines.\n\n\n\n"
            "And   more   spaces   everywhere."
        )
        result = compressor.compress(prompt)

        # Should not contain triple+ spaces
        assert "   " not in result.compressed_prompt

    def test_empty_prompt_handling(self, compressor: PromptCompressor) -> None:
        """Empty-ish prompts should be handled gracefully."""
        prompt = "Hi"
        result = compressor.compress(prompt)
        assert result.compressed_prompt == prompt
