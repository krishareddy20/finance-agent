"""
VectorMemory — ChromaDB-backed semantic memory for the finance agent.

Instead of storing decisions as plain text and doing exact-match lookups,
we embed every transaction decision as a vector. When a new transaction
arrives, we retrieve the K most semantically similar past decisions and
use them as context for the LLM — this is RAG (Retrieval-Augmented Generation).

Why this matters:
  - "Swiggy food order ₹350" and "Zomato delivery ₹420" are semantically
    similar even though they share no exact keywords. A vector search finds
    this; a SQL LIKE query doesn't.
  - The LLM gets richer, more relevant context → better decisions.
  - This is the same architecture used in production RAG systems at scale.

Architecture:
  Transaction text → TF-IDF embedding (local, free, fast)
               → ChromaDB collection
               → cosine similarity search at query time
               → top-K results returned as context string
"""

import json
import hashlib
from datetime import datetime
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class VectorMemory:
    """
    Semantic memory store backed by ChromaDB.
    Falls back to keyword search if ChromaDB is not installed.
    """

    COLLECTION_NAME = "finance_decisions"

    def __init__(self, persist_path: str = "./chroma_db"):
        self.persist_path = persist_path
        self._client      = None
        self._collection  = None
        self._fallback_store: list = []   # used if ChromaDB unavailable

        if CHROMA_AVAILABLE:
            self._init_chroma()
        else:
            print("  [VectorMemory] ChromaDB not installed — using keyword fallback.")
            print("  [VectorMemory] Run: pip install chromadb scikit-learn")

    # ── Initialisation ─────────────────────────────────────────────────────

    def _init_chroma(self):
        self._client = chromadb.PersistentClient(path=self.persist_path)
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},   # cosine similarity
        )
        print(f"  [VectorMemory] ChromaDB ready. "
              f"{self._collection.count()} decisions stored.")

    # ── Write ──────────────────────────────────────────────────────────────

    def store_decision(self, txn, decision: str, reasoning: str):
        """
        Embed and store a transaction decision.
        The document text combines description, merchant, category, and
        reasoning so that semantic search captures all dimensions.
        """
        doc_text = (
            f"{txn.description} {txn.merchant} {txn.category} "
            f"amount {txn.amount} decision {decision} {reasoning}"
        )
        doc_id = hashlib.md5(
            f"{txn.description}{txn.amount}{datetime.now().isoformat()}".encode()
        ).hexdigest()

        metadata = {
            "description": txn.description,
            "merchant":    txn.merchant or "",
            "category":    txn.category,
            "amount":      str(txn.amount),
            "decision":    decision,
            "reasoning":   reasoning,
            "timestamp":   datetime.now().isoformat(),
        }

        if CHROMA_AVAILABLE and self._collection is not None:
            self._collection.add(
                documents=[doc_text],
                metadatas=[metadata],
                ids=[doc_id],
            )
        else:
            self._fallback_store.append({
                "text": doc_text, "metadata": metadata, "id": doc_id
            })

    # ── Read ───────────────────────────────────────────────────────────────

    def retrieve_similar(self, txn, k: int = 5) -> str:
        """
        Find the K most semantically similar past decisions and return
        them as a formatted context string ready to inject into a prompt.
        """
        query = (
            f"{txn.description} {txn.merchant} {txn.category} "
            f"amount {txn.amount}"
        )

        if CHROMA_AVAILABLE and self._collection is not None:
            return self._chroma_search(query, k)
        else:
            return self._keyword_search(query, k)

    def _chroma_search(self, query: str, k: int) -> str:
        count = self._collection.count()
        if count == 0:
            return "No past decisions available."

        results = self._collection.query(
            query_texts=[query],
            n_results=min(k, count),
        )

        lines = ["Similar past decisions (retrieved via vector search):"]
        for meta, dist in zip(
            results["metadatas"][0],
            results["distances"][0],
        ):
            similarity = 1 - dist   # cosine distance → similarity
            lines.append(
                f"  • [{meta['decision'].upper()}] {meta['description']} "
                f"₹{meta['amount']} ({meta['category']}) "
                f"— {meta['reasoning']} "
                f"[similarity: {similarity:.2f}]"
            )
        return "\n".join(lines)

    def _keyword_search(self, query: str, k: int) -> str:
        """Simple TF-IDF fallback when ChromaDB is unavailable."""
        if not self._fallback_store:
            return "No past decisions available."

        if not SKLEARN_AVAILABLE:
            # Last resort: return most recent k decisions
            recent = self._fallback_store[-k:]
            lines = ["Recent past decisions (no vector search):"]
            for item in recent:
                m = item["metadata"]
                lines.append(f"  • [{m['decision'].upper()}] {m['description']} ₹{m['amount']}")
            return "\n".join(lines)

        texts = [item["text"] for item in self._fallback_store]
        texts_with_query = texts + [query]

        vec   = TfidfVectorizer(stop_words="english")
        tfidf = vec.fit_transform(texts_with_query)
        q_vec = tfidf[-1]
        scores = (tfidf[:-1] @ q_vec.T).toarray().flatten()

        top_k = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        lines = ["Similar past decisions (TF-IDF keyword search):"]
        for idx, score in top_k:
            m = self._fallback_store[idx]["metadata"]
            lines.append(
                f"  • [{m['decision'].upper()}] {m['description']} "
                f"₹{m['amount']} ({m['category']}) — {m['reasoning']} "
                f"[score: {score:.2f}]"
            )
        return "\n".join(lines)

    # ── Stats ──────────────────────────────────────────────────────────────

    def count(self) -> int:
        if CHROMA_AVAILABLE and self._collection is not None:
            return self._collection.count()
        return len(self._fallback_store)

    def get_stats(self) -> dict:
        return {
            "backend":    "ChromaDB" if CHROMA_AVAILABLE else "TF-IDF fallback",
            "total_docs": self.count(),
            "persist":    self.persist_path if CHROMA_AVAILABLE else "in-memory",
        }
