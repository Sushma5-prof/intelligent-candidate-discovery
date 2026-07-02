from app.models.career_history import CareerHistory
from app.services.ranking import score_candidate
from app.services.skill_graph import expand_skills, implicit_only


def test_expand_skills_adds_one_degree_inferences():
    expanded = expand_skills(["React"])
    assert "react" in expanded
    assert "javascript" in expanded


def test_implicit_only_excludes_explicit():
    implicit = implicit_only(["React", "JavaScript"])
    assert "javascript" not in implicit  # explicitly stated, not implicit
    assert "html" in implicit


def test_score_candidate_final_score_bounded_0_1():
    history = CareerHistory()
    history.add_role("Backend Engineer", 3.0, False)
    history.add_role("Senior Backend Engineer", 2.0, True)

    result = score_candidate(
        jd_text="Looking for a Python engineer with FastAPI and Docker experience.",
        jd_skill_vocab={"python", "fastapi", "docker"},
        semantic_score=0.9,
        candidate_explicit_skills=["Python", "FastAPI", "Docker"],
        career_history=history,
    )
    assert 0.0 <= result.final_score <= 1.0
    assert "python" in result.matched_explicit_skills
    assert result.final_score > 0.5  # strong match should score well


def test_score_candidate_zero_overlap_still_bounded():
    history = CareerHistory()
    history.add_role("Painter", 5.0, False)

    result = score_candidate(
        jd_text="Looking for a Rust systems engineer.",
        jd_skill_vocab={"rust"},
        semantic_score=0.05,
        candidate_explicit_skills=["Watercolor"],
        career_history=history,
    )
    assert result.implicit_skill_score == 0.0
    assert result.final_score >= 0.0
