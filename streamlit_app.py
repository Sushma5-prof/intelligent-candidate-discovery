import sys
import os
from pathlib import Path

# Add backend directory to path so we can import from app
backend_dir = str(Path(__file__).parent / "backend")
if backend_dir not in sys.path:
    sys.path.append(backend_dir)
os.chdir(backend_dir)


import time
import streamlit as st
import pandas as pd

from app.models.schemas import JobDescriptionRequest
from app.models.career_history import CareerHistory
from app.services import state
from app.services.ranking import score_candidate
from app.routers.search import _mask_pii, _rebuild_history

st.set_page_config(page_title="Intelligent Candidate Discovery", layout="wide")

@st.cache_resource
def load_backend_state():
    state.bootstrap()
    return state

# Initialize backend once
backend_state = load_backend_state()

st.title("Intelligent Candidate Discovery")
st.markdown("Sub-2.5s semantic candidate ranking with trajectory-aware reranking.")

# Sidebar controls
with st.sidebar:
    st.header("Search Settings")
    top_k = st.slider("Top K Semantic (Tier 1)", min_value=10, max_value=200, value=100, step=10)
    top_n = st.slider("Top N Final (Tier 3)", min_value=1, max_value=20, value=5, step=1)
    blind_mode = st.checkbox("Blind Audition Mode", value=False)
    
jd_text = st.text_area(
    "Job Description", 
    value="Senior Backend Engineer with Python, FastAPI, PostgreSQL and Docker experience. Kubernetes and AWS a plus.",
    height=150
)

if st.button("Search Candidates", type="primary"):
    with st.spinner("Searching..."):
        timings = {}
        
        # ---------------- Tier 1: The Net ----------------
        t0 = time.perf_counter()
        query_vector = backend_state.embedding_service.embed_query(jd_text)
        tier1_hits = backend_state.vector_store.search(query_vector, top_k=top_k)
        timings["tier1_net_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # ---------------- Tier 2: The Filter ----------------
        t0 = time.perf_counter()
        reranked = backend_state.reranker.rerank(jd_text, tier1_hits)
        timings["tier2_reranker_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # ---------------- Composite scoring (Sec. 4) ----------------
        t0 = time.perf_counter()
        scored_candidates = []
        for candidate, cross_encoder_score in reranked:
            history = _rebuild_history(candidate["roles"])

            score = score_candidate(
                jd_text=jd_text,
                jd_skill_vocab=backend_state.skill_vocab,
                semantic_score=cross_encoder_score,
                candidate_explicit_skills=candidate["explicit_skills"],
                career_history=history,
            )
            scored_candidates.append((candidate, score, history))

        scored_candidates.sort(key=lambda item: item[1].final_score, reverse=True)
        top_candidates = scored_candidates[:top_n]
        timings["scoring_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # ---------------- Tier 3: The Polish (top-N only) ----------------
        t0 = time.perf_counter()
        results = []
        for candidate, score, history in top_candidates:
            justification = backend_state.summarizer.summarize(
                jd_text=jd_text,
                name=candidate["name"],
                matched_explicit=score.matched_explicit_skills,
                matched_implicit=score.matched_implicit_skills,
                velocity_score=score.velocity_score,
                promotions=history.promotions,
                total_years=history.total_years,
            )

            name, email, location = candidate["name"], candidate["email"], candidate["location"]
            if blind_mode:
                name, email, location = _mask_pii(name, email, location)
                email = None
                
            results.append({
                "candidate": candidate,
                "score": score,
                "history": history,
                "justification": justification,
                "display_name": name,
                "display_email": email,
                "display_location": location
            })
            
        timings["tier3_polish_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        timings["total_ms"] = round(sum(timings.values()), 2)
        
        # Display Top Candidates
        st.subheader("Top Candidates")
        
        for idx, res in enumerate(results):
            score = res["score"]
            candidate = res["candidate"]
            history = res["history"]
            
            with st.container():
                st.markdown(f"### {idx+1}. {res['display_name']} - {candidate['headline']}")
                
                info_md = f"**Location:** {res['display_location']} | **Experience:** {round(history.total_years, 1)} years"
                if res['display_email']:
                    info_md += f" | **Email:** {res['display_email']}"
                st.markdown(info_md)
                
                scol1, scol2, scol3, scol4 = st.columns(4)
                scol1.metric("Final Score", round(score.final_score, 2))
                scol2.metric("Semantic Match", f"{round(score.semantic_score * 100)}%")
                scol3.metric("Explicit Skills Matched", len(score.matched_explicit_skills))
                scol4.metric("Velocity Score", round(score.velocity_score, 2))
                
                # Show skills inline
                skills_md = "**Matched Skills:** " + " ".join([f"`{s}`" for s in score.matched_explicit_skills])
                if score.matched_implicit_skills:
                    skills_md += " | **Inferred:** " + " ".join([f"`{s}*`" for s in score.matched_implicit_skills])
                st.markdown(skills_md)
                
                st.markdown("**Justification**")
                st.info(res["justification"])
                
                with st.expander("Score Breakdown & Details"):
                    st.json({
                        "score_breakdown": {
                            "final_score": score.final_score,
                            "semantic_score": score.semantic_score,
                            "velocity_score": score.velocity_score,
                            "matched_explicit_skills": score.matched_explicit_skills,
                            "matched_implicit_skills": score.matched_implicit_skills
                        },
                        "career_history": {
                            "total_years": history.total_years,
                            "promotions": history.promotions,
                            "roles": candidate["roles"]
                        },
                        "explicit_skills": candidate["explicit_skills"]
                    })
                st.divider()
                
        # Display Pipeline Metrics at the end
        st.subheader("Pipeline Metrics")
        st.markdown(
            f"""
            <div style="font-size: 14px; line-height: 1.6; color: #555555;">
            <strong>Total Latency:</strong> {timings['total_ms']} ms &nbsp;|&nbsp; 
            <strong>Tier 1 (Net):</strong> {timings['tier1_net_ms']} ms &nbsp;|&nbsp; 
            <strong>Tier 2 (Filter):</strong> {timings['tier2_reranker_ms']} ms &nbsp;|&nbsp; 
            <strong>Scoring:</strong> {timings['scoring_ms']} ms &nbsp;|&nbsp; 
            <strong>Tier 3 (Polish):</strong> {timings['tier3_polish_ms']} ms
            <br>
            <strong>Candidates Considered (Tier 1):</strong> {len(tier1_hits)} &nbsp;|&nbsp; 
            <strong>Candidates Reranked (Tier 2):</strong> {len(reranked)}
            </div>
            """,
            unsafe_allow_html=True
        )

