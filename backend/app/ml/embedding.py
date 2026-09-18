"""Text embedding with fastembed (primary) and a NumPy TF-IDF fallback."""

from __future__ import annotations

import re
from typing import Protocol

import numpy as np

FASTEMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> np.ndarray: ...


class FastEmbedEmbedder:
    """Multilingual sentence embeddings served via ONNX (no PyTorch dependency)."""

    def __init__(self) -> None:
        from fastembed import TextEmbedding  # local import keeps the API runtime light

        self._model = TextEmbedding(model_name=FASTEMBED_MODEL)

    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = list(self._model.embed(texts))
        return _normalize(np.asarray(vectors, dtype=np.float32))


class TfidfEmbedder:
    """Minimal TF-IDF vectorizer implemented with NumPy, used when fastembed is unavailable."""

    def __init__(self) -> None:
        self._vocab: dict[str, int] = {}
        self._idf: np.ndarray | None = None

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t for t in re.findall(r"[а-яёa-z0-9]+", text.lower()) if len(t) > 1]

    def fit(self, texts: list[str]) -> "TfidfEmbedder":
        tokenized = [self._tokenize(t) for t in texts]
        vocab = sorted({token for tokens in tokenized for token in tokens})
        self._vocab = {token: i for i, token in enumerate(vocab)}

        if not self._vocab:
            self._idf = np.zeros(0, dtype=np.float32)
            return self

        doc_count = len(texts)
        doc_freq = np.zeros(len(vocab), dtype=np.float32)
        for tokens in tokenized:
            for token in set(tokens):
                doc_freq[self._vocab[token]] += 1
        self._idf = np.log((doc_count + 1) / (doc_freq + 1)) + 1.0
        return self

    def transform(self, texts: list[str]) -> np.ndarray:
        rows = []
        for text in texts:
            vec = np.zeros(len(self._vocab), dtype=np.float32)
            for token in self._tokenize(text):
                idx = self._vocab.get(token)
                if idx is not None:
                    vec[idx] += 1
            rows.append(vec)
        term_freq = np.asarray(rows, dtype=np.float32)
        term_freq = term_freq / np.maximum(term_freq.sum(axis=1, keepdims=True), 1.0)
        return _normalize(term_freq * self._idf)

    def encode(self, texts: list[str]) -> np.ndarray:
        return self.transform(texts)


def build_embedder(corpus: list[str]) -> Embedder:
    """Return the best available embedder, preferring fastembed and falling back to TF-IDF."""
    try:
        embedder = FastEmbedEmbedder()
        embedder.encode(corpus[:1])  # trigger model download and verify it works
        return embedder
    except Exception:
        return TfidfEmbedder().fit(corpus)
