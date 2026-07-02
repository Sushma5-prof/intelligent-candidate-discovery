"""
Tier 2: "The Filter" -- cross-encoder reranking of the Tier 1 candidate pool.

Primary path: a locally hosted ONNX cross-encoder (ms-marco-MiniLM-L-6-v2)
via fastembed's TextCrossEncoder, jointly attending over (JD, candidate)
pairs for much higher precision than the bi-encoder cosine score alone.

Fallback path: if ONNX weights cannot be fetched, we approximate
cross-attention with a lightweight lexical overlap + TF-IDF pairwise
similarity signal. It is weaker than a true cross-encoder but keeps Tier 2
functional offline and produces scores in the same [0, 1] range, so
downstream ranking logic is unaffected.

Context-window truncation (PRD requirement) is applied to both paths to
bound latency on long JDs/resumes.
"""
from __future__ import annotations

import logging
import re
from typing import List, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MAX_CHARS = 1200  # context-window truncation for speed


def _truncate(text: str) -> str:
    return text[:MAX_CHARS]


class _OnnxCrossEncoderBackend:
    name = "onnx:ms-marco-MiniLM-L-6-v2"

    def __init__(self):
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self._model = TextCrossEncoder(model_name="Xenova/ms-marco-MiniLM-L-6-v2")

    def score(self, jd_text: str, candidate_texts: List[str]) -> List[float]:
        jd = _truncate(jd_text)
        docs = [_truncate(t) for t in candidate_texts]
        scores = list(self._model.rerank(jd, docs))
        return [float(_sigmoid(s)) for s in scores]


class _LexicalFallbackBackend:
    name = "lexical-tfidf (offline fallback)"

    def score(self, jd_text: str, candidate_texts: List[str]) -> List[float]:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        jd = _truncate(jd_text)
        docs = [_truncate(t) for t in candidate_texts]

        vectorizer = TfidfVectorizer(stop_words="english")
        matrix = vectorizer.fit_transform([jd] + docs)
        jd_vec, doc_vecs = matrix[0:1], matrix[1:]
        sims = cosine_similarity(jd_vec, doc_vecs)[0]

        # Blend in raw token overlap as a cheap proxy for cross-attention
        jd_tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+.#]{1,}", jd.lower()))
        overlaps = []
        for doc in docs:
            doc_tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9+.#]{1,}", doc.lower()))
            union = jd_tokens | doc_tokens
            overlaps.append(len(jd_tokens & doc_tokens) / len(union) if union else 0.0)

        blended = 0.7 * np.asarray(sims) + 0.3 * np.asarray(overlaps)
        return blended.clip(0, 1).tolist()


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


class CrossEncoderReranker:
    def __init__(self):
        try:
            self._backend = _OnnxCrossEncoderBackend()
            logger.info("CrossEncoderReranker using ONNX backend")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ONNX cross-encoder unavailable (%s). Falling back to lexical/TF-IDF reranking. "
                "For production precision, ensure outbound network access to fetch ONNX weights.",
                exc,
            )
            self._backend = _LexicalFallbackBackend()

    @property
    def backend_name(self) -> str:
        return self._backend.name

    def rerank(self, jd_text: str, candidates: List[dict]) -> List[Tuple[dict, float]]:
        texts = [c.get("summary", "") + " " + " ".join(c.get("explicit_skills", [])) for c in candidates]
        scores = self._backend.score(jd_text, texts)
        paired = list(zip(candidates, scores))
        paired.sort(key=lambda cs: cs[1], reverse=True)
        return paired
