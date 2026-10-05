"""Persistent local vector store backed by numpy + sentence-transformers."""

import json
import os
import threading

import numpy as np
from sentence_transformers import SentenceTransformer


class VectorStore:
    """A simple cosine-similarity vector store persisted to disk.

    Embeddings are L2-normalized on insert, so a dot product equals cosine
    similarity. Suitable for up to ~100k chunks on a single node.
    """

    def __init__(self, data_dir: str, embed_model: str):
        os.makedirs(data_dir, exist_ok=True)
        self._vec_path = os.path.join(data_dir, "vectors.npy")
        self._meta_path = os.path.join(data_dir, "meta.json")
        self._lock = threading.Lock()

        self.model = SentenceTransformer(embed_model)
        self.dim = self.model.get_sentence_embedding_dimension()
        self._load()

    def _load(self) -> None:
        if os.path.exists(self._vec_path) and os.path.exists(self._meta_path):
            self.vectors = np.load(self._vec_path)
            with open(self._meta_path, encoding="utf-8") as handle:
                self.meta = json.load(handle)
        else:
            self.vectors = np.zeros((0, self.dim), dtype="float32")
            self.meta = []

    def _save(self) -> None:
        np.save(self._vec_path, self.vectors)
        with open(self._meta_path, "w", encoding="utf-8") as handle:
            json.dump(self.meta, handle, ensure_ascii=False)

    def _embed(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        ).astype("float32")

    @property
    def count(self) -> int:
        return len(self.meta)

    def sources(self) -> list[str]:
        return sorted({item["source"] for item in self.meta})

    def add(self, items: list[dict]) -> int:
        """Adds chunk records (each needs source, chunk_index, text)."""
        texts = [item["text"] for item in items]
        if not texts:
            return 0
        embeddings = self._embed(texts)
        with self._lock:
            self.vectors = (
                np.vstack([self.vectors, embeddings])
                if len(self.vectors)
                else embeddings
            )
            self.meta.extend(items)
            self._save()
        return len(items)

    def remove_source(self, source: str) -> None:
        """Drops all chunks from a given source (for clean re-ingest)."""
        with self._lock:
            keep = [i for i, m in enumerate(self.meta) if m["source"] != source]
            self.vectors = (
                self.vectors[keep]
                if keep
                else np.zeros((0, self.dim), dtype="float32")
            )
            self.meta = [self.meta[i] for i in keep]
            self._save()

    def search(self, query: str, top_k: int) -> list[dict]:
        if len(self.vectors) == 0:
            return []
        query_vec = self._embed([query])[0]
        scores = self.vectors @ query_vec
        top = np.argsort(-scores)[:top_k]
        return [{**self.meta[i], "score": float(scores[i])} for i in top]
