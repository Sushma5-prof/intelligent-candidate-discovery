"""
Vectorization layer (Phase A) used to populate the Vector DB and to embed
incoming Job Descriptions at query time (Tier 1).

Primary path: FastEmbed running BAAI/bge-small-en-v1.5 locally via ONNX
Runtime -- no external API calls once weights are cached, so it satisfies
the "no API latency" requirement in the tech-stack table.

Fallback path: if the ONNX model weights cannot be downloaded (e.g. an
air-gapped CI box or a sandbox with restricted egress), we transparently
fall back to a TF-IDF vector space fit on the candidate corpus. The public
interface (`embed_documents` / `embed_query`) is identical either way, so
nothing downstream (vector store, reranker, ranking) needs to know which
backend is active. `EmbeddingService.backend_name` reports which is live.
"""
from __future__ import annotations

import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)


class _FastEmbedBackend:
    name = "fastembed:BAAI/bge-small-en-v1.5"

    def __init__(self, model_name: str):
        from fastembed import TextEmbedding  # imported lazily; heavy dep

        # specific_model_path/local_files_only isn't universally supported across
        # fastembed versions, so we bound the retry storm via env var instead.
        import os

        os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "5")
        self._model = TextEmbedding(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        return np.array(list(self._model.embed(texts)))

    def embed_query(self, text: str) -> np.ndarray:
        return np.array(list(self._model.query_embed(text)))[0]


class _TfidfBackend:
    """
    Offline-safe fallback. Not as semantically rich as a transformer
    embedding, but keeps the two-stage retrieval architecture fully
    functional with zero network dependency, and is dimensionally fixed
    via SVD so it is a drop-in replacement for Qdrant's HNSW index.
    """

    name = "tfidf+svd (offline fallback)"

    def __init__(self, target_dim: int = 384):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD

        self._vectorizer = TfidfVectorizer(max_features=20000, stop_words="english")
        self._target_dim = target_dim
        self._svd: "TruncatedSVD | None" = None
        self._fitted = False

    def fit(self, corpus: List[str]) -> None:
        from sklearn.decomposition import TruncatedSVD

        tfidf_matrix = self._vectorizer.fit_transform(corpus)
        n_components = min(self._target_dim, tfidf_matrix.shape[1] - 1, tfidf_matrix.shape[0] - 1)
        n_components = max(n_components, 2)
        self._svd = TruncatedSVD(n_components=n_components, random_state=42)
        self._svd.fit(tfidf_matrix)
        self._fitted = True

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        if not self._fitted:
            self.fit(texts)
        tfidf_matrix = self._vectorizer.transform(texts)
        vectors = self._svd.transform(tfidf_matrix)
        return self._l2_normalize(vectors)

    def embed_query(self, text: str) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("TfidfBackend must be fit on the corpus before embedding queries.")
        tfidf_vec = self._vectorizer.transform([text])
        vec = self._svd.transform(tfidf_vec)[0]
        return self._l2_normalize(vec.reshape(1, -1))[0]

    @staticmethod
    def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms


class EmbeddingService:
    def __init__(self, model_name: str):
        try:
            self._backend = _FastEmbedBackend(model_name)
            logger.info("EmbeddingService using FastEmbed backend (%s)", model_name)
        except Exception as exc:  # noqa: BLE001 - broad on purpose, this is an env fallback
            logger.warning(
                "FastEmbed unavailable (%s). Falling back to offline TF-IDF embeddings. "
                "For production-quality semantic search, ensure outbound network access "
                "to fetch ONNX model weights.",
                exc,
            )
            self._backend = _TfidfBackend()

    @property
    def backend_name(self) -> str:
        return self._backend.name

    @property
    def dim(self) -> int | None:
        return getattr(self._backend, "_target_dim", None)

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        return np.asarray(self._backend.embed_documents(texts))

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(self._backend.embed_query(text))
