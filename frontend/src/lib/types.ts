export interface ScoreBreakdown {
  semantic_score: number;
  implicit_skill_score: number;
  velocity_score: number;
  hop_penalty: number;
  final_score: number;
  matched_explicit_skills: string[];
  matched_implicit_skills: string[];
}

export interface RankedCandidate {
  id: string;
  name: string;
  email: string | null;
  location: string;
  headline: string;
  total_years_experience: number;
  promotions: number;
  avg_tenure_years: number;
  score_breakdown: ScoreBreakdown;
  justification: string;
}

export interface SearchResponse {
  query_preview: string;
  candidates_considered_tier1: number;
  candidates_reranked_tier2: number;
  results: RankedCandidate[];
  blind_mode: boolean;
  latency_ms: Record<string, number>;
}

export interface SearchRequest {
  jd_text: string;
  top_k_semantic?: number;
  top_n_final?: number;
  blind_mode?: boolean;
}
