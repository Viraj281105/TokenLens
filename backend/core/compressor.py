"""
TokenLens — Layer 1: Prompt Compression Engine
================================================
Reduces token count by 25-40% through:
  - Filler phrase removal
  - Redundant whitespace elimination
  - TF-IDF sentence importance scoring with extractive compression
  - Safety floor: never compress below 60% of original length
"""

from __future__ import annotations

import logging
import re
from typing import Final

import tiktoken
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.models.schemas import CompressionResult

logger = logging.getLogger("tokenlens.compressor")

# ── Constants ──────────────────────────────────────────────────────────

ENCODING_NAME: Final[str] = "cl100k_base"
MIN_RETENTION_RATIO: Final[float] = 0.60  # Never compress below 60%
MIN_SENTENCES_FOR_TFIDF: Final[int] = 3   # Need at least 3 sentences for TF-IDF

# Filler phrases to strip (case-insensitive)
FILLER_PHRASES: Final[list[str]] = [
    r"\bbasically\b",
    r"\bessentially\b",
    r"\bactually\b",
    r"\bliterally\b",
    r"\bjust\b",
    r"\breally\b",
    r"\bsimply\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\byou know\b",
    r"\bi mean\b",
    r"\bin other words\b",
    r"\bas a matter of fact\b",
    r"\bit is worth noting that\b",
    r"\bit should be noted that\b",
    r"\bit is important to note that\b",
    r"\bneedless to say\b",
    r"\bfor what it's worth\b",
    r"\bat the end of the day\b",
    r"\ball things considered\b",
    r"\bin my opinion\b",
    r"\bto be honest\b",
    r"\bto tell you the truth\b",
    r"\bthe fact of the matter is\b",
    r"\bas you can see\b",
    r"\bas i mentioned before\b",
    r"\bas previously stated\b",
    r"\bplease note that\b",
    r"\bplease be aware that\b",
    r"\bi would like to\b",
    r"\bi want to\b",
    r"\bcould you please\b",
    r"\bwould you mind\b",
    r"\bif you don't mind\b",
    r"\bi was wondering if\b",
]

# Pre-compile filler patterns for performance
_FILLER_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(p, re.IGNORECASE) for p in FILLER_PHRASES
]


class PromptCompressor:
    """
    Intelligent prompt compressor that reduces token count while
    preserving semantic meaning.
    """

    def __init__(self) -> None:
        self._encoder = tiktoken.get_encoding(ENCODING_NAME)
        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
        )
        logger.info("PromptCompressor initialized with %s encoding", ENCODING_NAME)

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken cl100k_base encoding."""
        return len(self._encoder.encode(text))

    def compress(self, prompt: str) -> CompressionResult:
        """
        Run the full compression pipeline:
        1. Count original tokens
        2. Remove filler phrases
        3. Normalize whitespace
        4. Apply TF-IDF sentence scoring (if enough sentences)
        5. Enforce 60% minimum retention
        6. Count compressed tokens

        Returns a CompressionResult with before/after metrics.
        """
        original_tokens = self.count_tokens(prompt)

        if original_tokens <= 20:
            # Too short to compress meaningfully
            return CompressionResult(
                compressed_prompt=prompt,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
            )

        # Stage 1: Remove filler phrases
        compressed = self._remove_fillers(prompt)

        # Stage 2: Normalize whitespace
        compressed = self._normalize_whitespace(compressed)

        # Stage 3: TF-IDF extractive compression
        compressed = self._tfidf_compress(compressed, original_tokens)

        # Stage 4: Enforce minimum retention
        compressed = self._enforce_minimum_retention(prompt, compressed, original_tokens)

        compressed_tokens = self.count_tokens(compressed)

        # Safety: if compression somehow increased tokens, return original
        if compressed_tokens >= original_tokens:
            return CompressionResult(
                compressed_prompt=prompt,
                original_tokens=original_tokens,
                compressed_tokens=original_tokens,
                compression_ratio=1.0,
            )

        compression_ratio = compressed_tokens / original_tokens if original_tokens > 0 else 1.0

        logger.info(
            "Compressed %d → %d tokens (%.1f%% ratio)",
            original_tokens,
            compressed_tokens,
            compression_ratio * 100,
        )

        return CompressionResult(
            compressed_prompt=compressed,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=round(compression_ratio, 4),
        )

    def _remove_fillers(self, text: str) -> str:
        """Remove filler phrases from text."""
        result = text
        for pattern in _FILLER_PATTERNS:
            result = pattern.sub("", result)
        return result

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse multiple spaces, tabs, and excessive newlines."""
        # Collapse multiple spaces to single
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse 3+ newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Strip lines
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    def _tfidf_compress(self, text: str, original_tokens: int) -> str:
        """
        Score sentences by TF-IDF importance and keep the most
        important ones to hit the target token count.
        """
        sentences = self._split_sentences(text)

        if len(sentences) < MIN_SENTENCES_FOR_TFIDF:
            return text

        try:
            tfidf_matrix = self._vectorizer.fit_transform(sentences)
        except ValueError:
            # Empty vocabulary — all stop words or too short
            return text

        # Score each sentence by sum of its TF-IDF feature values
        scores = tfidf_matrix.sum(axis=1).A1.tolist()  # type: ignore[union-attr]

        # Pair sentences with scores and original indices
        scored = list(enumerate(zip(sentences, scores)))

        # Sort by score descending
        scored.sort(key=lambda x: x[1][1], reverse=True)

        # Calculate target token count (keep ~70% of tokens)
        target_tokens = int(original_tokens * 0.70)

        # Select top sentences until we reach target
        selected_indices: list[int] = []
        current_tokens = 0

        for idx, (sentence, _score) in scored:
            sentence_tokens = self.count_tokens(sentence)
            if current_tokens + sentence_tokens <= target_tokens:
                selected_indices.append(idx)
                current_tokens += sentence_tokens

            if current_tokens >= target_tokens:
                break

        # If we selected nothing, keep at least the top sentence
        if not selected_indices and scored:
            selected_indices.append(scored[0][0])

        # Reconstruct in original order
        selected_indices.sort()
        result = " ".join(sentences[i] for i in selected_indices)

        return result

    def _enforce_minimum_retention(
        self, original: str, compressed: str, original_tokens: int
    ) -> str:
        """Ensure we never compress below 60% of original token count."""
        compressed_tokens = self.count_tokens(compressed)
        min_tokens = int(original_tokens * MIN_RETENTION_RATIO)

        if compressed_tokens >= min_tokens:
            return compressed

        # If too aggressive, fall back to just filler removal + whitespace
        fallback = self._remove_fillers(original)
        fallback = self._normalize_whitespace(fallback)
        fallback_tokens = self.count_tokens(fallback)

        if fallback_tokens >= min_tokens:
            return fallback

        # Last resort: return original
        return original

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Split text into sentences using regex."""
        # Split on period, exclamation, question mark followed by space or end
        raw = re.split(r"(?<=[.!?])\s+", text)
        # Filter empty strings
        return [s.strip() for s in raw if s.strip()]
