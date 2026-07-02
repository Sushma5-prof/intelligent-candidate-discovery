from typing import List, Optional
from pydantic import BaseModel, Field


class RoleInput(BaseModel):
    title: str
    duration_years: float = Field(ge=0)
    is_promotion: bool = False


class CandidateProfile(BaseModel):
    """Canonical shape produced by Phase A ingestion (resume -> strict JSON)."""
    id: str
    name: str
    email: str
    location: str
    headline: str
    summary: str
    explicit_skills: List[str]
    roles: List[RoleInput]


class JobDescriptionRequest(BaseModel):
    jd_text: str = Field(min_length=10, description="Full job description text")
    top_k_semantic: int = Field(default=100, ge=1, le=500, description="Tier 1 candidate pool size")
    top_n_final: int = Field(default=5, ge=1, le=50, description="Final ranked list size")
    blind_mode: bool = Field(default=False, description="Mask PII for algorithmic fairness review")


class ScoreBreakdown(BaseModel):
    semantic_score: float
    implicit_skill_score: float
    velocity_score: float
    hop_penalty: float
    final_score: float
    matched_explicit_skills: List[str]
    matched_implicit_skills: List[str]


class RankedCandidate(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    location: str
    headline: str
    total_years_experience: float
    promotions: int
    avg_tenure_years: float
    score_breakdown: ScoreBreakdown
    justification: str


class SearchResponse(BaseModel):
    query_preview: str
    candidates_considered_tier1: int
    candidates_reranked_tier2: int
    results: List[RankedCandidate]
    blind_mode: bool
    latency_ms: dict
