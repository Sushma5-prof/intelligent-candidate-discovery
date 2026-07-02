"""
Tier 1: "The Net" -- fast HNSW vector search.

Uses qdrant-client's embedded `:memory:` mode for the hackathon POC so no
external server process is required. In production, swap the `location`
argument for a real Qdrant/Milvus endpoint (see README) with zero code
changes elsewhere in the pipeline.
"""
from __future__ import annotations

from typing import List

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels


class VectorStore:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.client = QdrantClient(location=":memory:")
        self._dim: int | None = None

    def build_index(self, ids: List[str], vectors: np.ndarray, payloads: List[dict]) -> None:
        dim = vectors.shape[1]
        self._dim = dim

        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=qmodels.VectorParams(size=dim, distance=qmodels.Distance.COSINE),
        )

        points = [
            qmodels.PointStruct(id=idx, vector=vectors[idx].tolist(), payload={**payloads[idx], "_id": ids[idx]})
            for idx in range(len(ids))
        ]
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query_vector: np.ndarray, top_k: int) -> List[dict]:
        hits = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k,
            with_payload=True,
        )
        return [{"score": hit.score, **hit.payload} for hit in hits]
