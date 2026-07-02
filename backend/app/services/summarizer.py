"""
Tier 3: "The Polish" -- 2-sentence AI-generated justification for the top-N
candidates only (keeps LLM calls off the hot path for the other 95+
candidates in the Tier 1 pool, per the PRD's latency budget).

Primary path: Groq API running Llama 3 8B (~300ms per PRD tech-stack table).
Fallback path: if GROQ_API_KEY is not configured (or the call fails/times
out), we generate a deterministic template summary from the same score
breakdown the LLM would have seen -- still explainable, just not
LLM-phrased. This keeps the Explainability Dashboard fully functional in
demo/offline environments.
"""
from __future__ import annotations

import logging
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


def _template_summary(name: str, matched_explicit: List[str], matched_implicit: List[str],
                       velocity_score: float, promotions: int, total_years: float) -> str:
    skill_bits = matched_explicit[:3]
    skill_str = ", ".join(skill_bits) if skill_bits else "relevant background"
    implicit_str = f", inferring {', '.join(matched_implicit[:2])}" if matched_implicit else ""
    velocity_str = (
        f"{promotions} promotion(s) across {total_years:.1f} years"
        if promotions
        else f"{total_years:.1f} years of steady tenure"
    )
    return (
        f"{name} matches this role primarily on {skill_str}{implicit_str}. "
        f"Career trajectory shows {velocity_str}, yielding a velocity score of {velocity_score:.2f}."
    )


class ExplainabilitySummarizer:
    def __init__(self):
        self._client = None
        if settings.groq_api_key:
            try:
                from groq import Groq

                self._client = Groq(api_key=settings.groq_api_key)
                logger.info("ExplainabilitySummarizer using Groq (%s)", settings.groq_model)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Groq client init failed (%s); using template fallback.", exc)
        else:
            logger.info("GROQ_API_KEY not set; ExplainabilitySummarizer using template fallback.")

    def summarize(self, jd_text: str, name: str, matched_explicit: List[str],
                  matched_implicit: List[str], velocity_score: float, promotions: int,
                  total_years: float) -> str:
        fallback = _template_summary(name, matched_explicit, matched_implicit, velocity_score,
                                      promotions, total_years)
        if not self._client:
            return fallback

        prompt = (
            "You are a technical recruiting assistant. In exactly 2 concise sentences, "
            f"explain why candidate '{name}' is a strong fit for this job description. "
            f"Ground your answer in these facts only: matched skills = {matched_explicit}, "
            f"inferred skills = {matched_implicit}, promotions = {promotions}, "
            f"total years experience = {total_years:.1f}, velocity score (0-1) = {velocity_score:.2f}.\n\n"
            f"Job description:\n{jd_text[:800]}"
        )
        try:
            completion = self._client.chat.completions.create(
                model=settings.groq_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=120,
                temperature=0.4,
            )
            text = completion.choices[0].message.content.strip()
            return text or fallback
        except Exception as exc:  # noqa: BLE001
            logger.warning("Groq summarization failed (%s); using template fallback.", exc)
            return fallback
