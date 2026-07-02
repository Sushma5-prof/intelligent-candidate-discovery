import time
import logging

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import (
    JobDescriptionRequest, SearchResponse, RankedCandidate, ScoreBreakdown,
)
from app.models.career_history import CareerHistory
from app.services import state
from app.services.ranking import score_candidate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["search"])


def _mask_pii(name: str, email: str, location: str) -> tuple[str, str, str]:
    initials = "".join(part[0] for part in name.split() if part).upper()
    return f"Candidate {initials}***", "hidden@blind-audition", location.split(",")[-1].strip()


@router.post("/search", response_model=SearchResponse)
def search_candidates(request: JobDescriptionRequest) -> SearchResponse:
    timings: dict[str, float] = {}

    # ---------------- Tier 1: The Net ----------------
    t0 = time.perf_counter()
    query_vector = state.embedding_service.embed_query(request.jd_text)
    tier1_hits = state.vector_store.search(query_vector, top_k=request.top_k_semantic)
    timings["tier1_net_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # ---------------- Tier 2: The Filter ----------------
    t0 = time.perf_counter()
    reranked = state.reranker.rerank(request.jd_text, tier1_hits)
    timings["tier2_reranker_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # ---------------- Composite scoring (Sec. 4) ----------------
    t0 = time.perf_counter()
    scored_candidates = []
    for candidate, cross_encoder_score in reranked:
        history: CareerHistory = _rebuild_history(candidate["roles"])

        score = score_candidate(
            jd_text=request.jd_text,
            jd_skill_vocab=state.skill_vocab,
            semantic_score=cross_encoder_score,
            candidate_explicit_skills=candidate["explicit_skills"],
            career_history=history,
        )
        scored_candidates.append((candidate, score, history))

    scored_candidates.sort(key=lambda item: item[1].final_score, reverse=True)
    top_candidates = scored_candidates[: request.top_n_final]
    timings["scoring_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    # ---------------- Tier 3: The Polish (top-N only) ----------------
    t0 = time.perf_counter()
    results = []
    for candidate, score, history in top_candidates:
        justification = state.summarizer.summarize(
            jd_text=request.jd_text,
            name=candidate["name"],
            matched_explicit=score.matched_explicit_skills,
            matched_implicit=score.matched_implicit_skills,
            velocity_score=score.velocity_score,
            promotions=history.promotions,
            total_years=history.total_years,
        )

        name, email, location = candidate["name"], candidate["email"], candidate["location"]
        if request.blind_mode:
            name, email, location = _mask_pii(name, email, location)

        results.append(
            RankedCandidate(
                id=candidate["_id"],
                name=name,
                email=None if request.blind_mode else email,
                location=location,
                headline=candidate["headline"],
                total_years_experience=round(history.total_years, 1),
                promotions=history.promotions,
                avg_tenure_years=round(history.total_years / history.role_count, 2) if history.role_count else 0.0,
                score_breakdown=ScoreBreakdown(**score.__dict__),
                justification=justification,
            )
        )
    timings["tier3_polish_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    timings["total_ms"] = round(sum(timings.values()), 2)

    return SearchResponse(
        query_preview=request.jd_text[:160],
        candidates_considered_tier1=len(tier1_hits),
        candidates_reranked_tier2=len(reranked),
        results=results,
        blind_mode=request.blind_mode,
        latency_ms=timings,
    )


def _rebuild_history(roles: list[dict]) -> CareerHistory:
    history = CareerHistory()
    for role in roles:
        history.add_role(role["title"], role["duration_years"], role["is_promotion"])
    return history
