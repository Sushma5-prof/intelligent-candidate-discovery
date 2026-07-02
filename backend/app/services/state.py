"""
Holds the process-wide singletons built during Phase A ingestion:
embedding backend, populated vector index, reranker, and summarizer.
Populated once by `bootstrap()`, called from the FastAPI startup event.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Set

from app.config import settings
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.reranker import CrossEncoderReranker
from app.services.summarizer import ExplainabilitySummarizer
from app.services.skill_graph import SKILL_GRAPH

logger = logging.getLogger(__name__)

embedding_service: EmbeddingService | None = None
vector_store: VectorStore | None = None
reranker: CrossEncoderReranker | None = None
summarizer: ExplainabilitySummarizer | None = None
skill_vocab: Set[str] = set()


def bootstrap() -> None:
    global embedding_service, vector_store, reranker, summarizer, skill_vocab

    data_path = Path(settings.data_path)
    if not data_path.exists():
        # Auto-generate on first run so `uvicorn app.main:app` just works.
        from app.data.generate_synthetic_data import main as generate_data

        generate_data(count=settings.synthetic_candidate_count, out_path=str(data_path))

    candidates = json.loads(data_path.read_text())
    logger.info("Loaded %d candidates from %s", len(candidates), data_path)

    embedding_service = EmbeddingService(settings.embedding_model_name)

    corpus = [
        f"{c['headline']}. {c['summary']} Skills: {', '.join(c['explicit_skills'])}"
        for c in candidates
    ]
    vectors = embedding_service.embed_documents(corpus)

    vector_store = VectorStore(settings.qdrant_collection)
    ids = [c["id"] for c in candidates]
    vector_store.build_index(ids, vectors, candidates)

    reranker = CrossEncoderReranker()
    summarizer = ExplainabilitySummarizer()

    # Vocabulary of every skill token our skill graph knows about + anything
    # any candidate explicitly listed -- used to spot skill mentions in JD text.
    skill_vocab = set(SKILL_GRAPH.keys())
    for c in candidates:
        skill_vocab.update(s.lower() for s in c["explicit_skills"])

    logger.info(
        "Bootstrap complete. embedding backend=%s reranker backend=%s",
        embedding_service.backend_name,
        reranker.backend_name,
    )
