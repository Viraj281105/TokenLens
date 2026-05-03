"""
TokenLens — Layer 2: Semantic Cache
=====================================
FAISS-backed similarity cache with LRU eviction.
Embeds prompts with sentence-transformers (all-MiniLM-L6-v2),
stores in IndexFlatIP, and returns cached responses on ≥ 0.92 cosine hits.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Final, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from backend.models.schemas import CacheResult

logger = logging.getLogger("tokenlens.cache")

# ── Constants ──────────────────────────────────────────────────────────

SIMILARITY_THRESHOLD: Final[float] = 0.92
MAX_CACHE_SIZE: Final[int] = 1000
EMBEDDING_MODEL: Final[str] = "all-MiniLM-L6-v2"
EMBEDDING_DIM: Final[int] = 384  # all-MiniLM-L6-v2 output dimension


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""
    prompt_hash: str
    prompt: str
    response: str
    embedding: np.ndarray
    timestamp: float = field(default_factory=time.time)
    tokens_saved: int = 0
    hit_count: int = 0


class SemanticCache:
    """
    FAISS-based semantic cache with LRU eviction policy.
    Thread-safe via a reentrant lock for concurrent access.
    """

    def __init__(self, model_name: str = EMBEDDING_MODEL) -> None:
        self._lock = threading.RLock()
        self._model = SentenceTransformer(model_name)
        self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._id_to_hash: list[str] = []  # Maps FAISS index → prompt_hash

        # Stats
        self._total_queries: int = 0
        self._total_hits: int = 0
        self._total_tokens_saved: int = 0

        logger.info(
            "SemanticCache initialized: model=%s, dim=%d, threshold=%.2f",
            model_name, EMBEDDING_DIM, SIMILARITY_THRESHOLD,
        )

    def _embed(self, text: str) -> np.ndarray:
        """Generate normalized embedding for text."""
        embedding = self._model.encode(
            text, normalize_embeddings=True, show_progress_bar=False
        )
        return np.array(embedding, dtype=np.float32).reshape(1, -1)

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        """SHA-256 hash of the prompt."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

    def get(self, prompt: str, original_tokens: int = 0) -> CacheResult:
        """
        Look up a prompt in the cache via semantic similarity.

        Returns CacheResult with cache_hit=True if similarity ≥ threshold.
        """
        with self._lock:
            self._total_queries += 1

            if self._index.ntotal == 0:
                return CacheResult(cache_hit=False)

            query_embedding = self._embed(prompt)

            # Search for the single nearest neighbor
            similarities, indices = self._index.search(query_embedding, 1)
            best_similarity = float(similarities[0][0])
            best_idx = int(indices[0][0])

            if best_similarity >= SIMILARITY_THRESHOLD and 0 <= best_idx < len(self._id_to_hash):
                prompt_hash = self._id_to_hash[best_idx]
                entry = self._entries.get(prompt_hash)

                if entry is not None:
                    # Move to end (most recently used)
                    self._entries.move_to_end(prompt_hash)
                    entry.hit_count += 1
                    self._total_hits += 1
                    self._total_tokens_saved += original_tokens

                    logger.info(
                        "Cache HIT: similarity=%.4f, hash=%s, tokens_saved=%d",
                        best_similarity, prompt_hash, original_tokens,
                    )

                    return CacheResult(
                        cache_hit=True,
                        cached_response=entry.response,
                        similarity_score=round(best_similarity, 4),
                        tokens_saved=original_tokens,
                    )

            logger.debug("Cache MISS: best_similarity=%.4f", best_similarity)
            return CacheResult(cache_hit=False, similarity_score=round(best_similarity, 4))

    def set(self, prompt: str, response: str, tokens_saved: int = 0) -> None:
        """
        Store a prompt-response pair in the cache.
        Evicts LRU entry if at max capacity.
        """
        with self._lock:
            prompt_hash = self._hash_prompt(prompt)

            # Skip if already cached
            if prompt_hash in self._entries:
                self._entries.move_to_end(prompt_hash)
                return

            # Evict LRU if at capacity
            if len(self._entries) >= MAX_CACHE_SIZE:
                self._evict_lru()

            embedding = self._embed(prompt)

            entry = CacheEntry(
                prompt_hash=prompt_hash,
                prompt=prompt,
                response=response,
                embedding=embedding.flatten(),
                tokens_saved=tokens_saved,
            )

            self._entries[prompt_hash] = entry
            self._index.add(embedding)
            self._id_to_hash.append(prompt_hash)

            logger.info("Cache SET: hash=%s, entries=%d", prompt_hash, len(self._entries))

    def _evict_lru(self) -> None:
        """Remove the least recently used entry and rebuild the FAISS index."""
        if not self._entries:
            return

        evicted_hash, evicted_entry = self._entries.popitem(last=False)
        logger.info("Cache EVICT (LRU): hash=%s", evicted_hash)

        # Remove from id mapping
        if evicted_hash in self._id_to_hash:
            self._id_to_hash.remove(evicted_hash)

        # Rebuild FAISS index from remaining entries
        self._rebuild_index()

    def _rebuild_index(self) -> None:
        """Rebuild the FAISS index from current entries."""
        self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
        new_id_to_hash: list[str] = []

        for prompt_hash, entry in self._entries.items():
            embedding = entry.embedding.reshape(1, -1)
            self._index.add(embedding)
            new_id_to_hash.append(prompt_hash)

        self._id_to_hash = new_id_to_hash

    def stats(self) -> dict:
        """Return cache performance statistics."""
        with self._lock:
            hit_rate = (
                (self._total_hits / self._total_queries * 100)
                if self._total_queries > 0
                else 0.0
            )
            return {
                "total_queries": self._total_queries,
                "total_hits": self._total_hits,
                "hit_rate": round(hit_rate, 2),
                "tokens_saved_via_cache": self._total_tokens_saved,
                "cache_size": len(self._entries),
                "max_size": MAX_CACHE_SIZE,
            }

    def clear(self) -> None:
        """Clear all cache entries and reset stats."""
        with self._lock:
            self._entries.clear()
            self._id_to_hash.clear()
            self._index = faiss.IndexFlatIP(EMBEDDING_DIM)
            self._total_queries = 0
            self._total_hits = 0
            self._total_tokens_saved = 0
            logger.info("Cache cleared")
