"""
Section 4 - The Ranking Algorithm.

FinalScore = (alpha * S_semantic) + (beta * S_implicit) + (gamma * S_velocity) - P_hop

Design notes:
- S_semantic is taken from the Tier 2 cross-encoder score (higher precision
  than the raw Tier 1 cosine similarity used only to build the candidate pool).
- S_implicit is a Jaccard-style overlap between the JD's inferred skill set
  and the candidate's inferred skill set (expand_skills), so a candidate who
  lists "React" gets credit against a JD asking for "JavaScript" even though
  the literal string never appears on their resume.
- S_velocity / P_hop come directly from CareerHistory.calculate_velocity(),
  which already folds the job-hopping penalty into its own return value; we
  surface hop_penalty separately here purely for explainability.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Set

from app.config import settings
from app.models.career_history import CareerHistory
from app.services.skill_graph import expand_skills


@dataclass
class ScoreResult:
    semantic_score: float
    implicit_skill_score: float
    velocity_score: float
    hop_penalty: float
    final_score: float
    matched_explicit_skills: List[str]
    matched_implicit_skills: List[str]


_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#]{1,}")


def _extract_jd_skill_hints(jd_text: str, known_skills: Set[str]) -> Set[str]:
    """Cheap keyword extraction: any known vocabulary skill token mentioned in the JD."""
    tokens = {t.lower() for t in _WORD_RE.findall(jd_text)}
    return {s for s in known_skills if s in tokens}


def build_career_history(roles: list) -> CareerHistory:
    history = CareerHistory()
    # Preserve chronological order in the linked list (oldest first added last
    # so `.titles()` yields most-recent-first, matching resume convention).
    for role in roles:
        history.add_role(role.title, role.duration_years, role.is_promotion)
    return history


def score_candidate(
    jd_text: str,
    jd_skill_vocab: Set[str],
    semantic_score: float,
    candidate_explicit_skills: List[str],
    career_history: CareerHistory,
) -> ScoreResult:
    # --- S_implicit: expanded-skill Jaccard overlap ---
    jd_skills_mentioned = _extract_jd_skill_hints(jd_text, jd_skill_vocab)
    jd_expanded = expand_skills(list(jd_skills_mentioned)) if jd_skills_mentioned else set()
    candidate_expanded = expand_skills(candidate_explicit_skills)

    if jd_expanded:
        overlap = jd_expanded & candidate_expanded
        union = jd_expanded | candidate_expanded
        implicit_score = len(overlap) / len(union) if union else 0.0
    else:
        overlap = set()
        implicit_score = 0.0

    matched_explicit = sorted(overlap & {s.lower() for s in candidate_explicit_skills})
    matched_implicit = sorted(overlap - matched_explicit_set(candidate_explicit_skills))

    # --- S_velocity (hop penalty already folded in by CareerHistory) ---
    velocity_score = career_history.calculate_velocity()

    # Recover the raw (pre-penalty) hop penalty purely for the explainability UI
    avg_tenure = (
        career_history.total_years / career_history.role_count if career_history.role_count else 0.0
    )
    hop_penalty = 0.2 if (career_history.role_count and avg_tenure < 1.0) else 0.0

    final_score = (
        settings.weight_semantic * semantic_score
        + settings.weight_implicit * implicit_score
        + settings.weight_velocity * velocity_score
    ) - hop_penalty
    final_score = max(0.0, min(1.0, final_score))

    return ScoreResult(
        semantic_score=round(semantic_score, 4),
        implicit_skill_score=round(implicit_score, 4),
        velocity_score=round(velocity_score, 4),
        hop_penalty=round(hop_penalty, 4),
        final_score=round(final_score, 4),
        matched_explicit_skills=matched_explicit,
        matched_implicit_skills=matched_implicit,
    )


def matched_explicit_set(candidate_explicit_skills: List[str]) -> Set[str]:
    return {s.lower() for s in candidate_explicit_skills}
