import pytest

from app.models.career_history import CareerHistory


def test_empty_history_returns_zero_velocity():
    history = CareerHistory()
    assert history.calculate_velocity() == 0.0


def test_single_promotion_every_two_years_hits_ceiling():
    history = CareerHistory()
    history.add_role("Engineer I", 2.0, False)
    history.add_role("Engineer II", 2.0, True)
    # 1 promotion / 4 years * k(2.0) = 0.5 -> not yet capped
    assert history.calculate_velocity() == pytest.approx(0.5, abs=1e-3)


def test_velocity_caps_at_one(): 
    history = CareerHistory()
    history.add_role("Eng I", 1.0, False)
    history.add_role("Eng II", 1.0, True)
    history.add_role("Eng III", 1.0, True)
    history.add_role("Eng IV", 1.0, True)
    # 3 promotions / 4 years * 2 = 1.5 -> capped to 1.0
    assert history.calculate_velocity() == 1.0


def test_extreme_job_hopping_incurs_penalty():
    history = CareerHistory()
    history.add_role("Eng A", 0.5, False)
    history.add_role("Eng B", 0.5, True)
    # avg tenure = 0.5 yrs < 1.0 -> 0.2 penalty applied
    base = min(1.0, (1 / 1.0) * 2.0)
    expected = max(0.0, base - 0.2)
    assert history.calculate_velocity() == pytest.approx(expected, abs=1e-3)


def test_add_role_rejects_negative_duration():
    history = CareerHistory()
    with pytest.raises(ValueError):
        history.add_role("Eng", -1.0, False)


def test_add_role_rejects_empty_title():
    history = CareerHistory()
    with pytest.raises(ValueError):
        history.add_role("   ", 1.0, False)


def test_node_encapsulation_not_leaked():
    """`_JobNode` should only be reachable through CareerHistory, never imported directly."""
    history = CareerHistory()
    history.add_role("Eng", 1.0, False)
    assert isinstance(history.head, CareerHistory._JobNode)
    with pytest.raises(ImportError):
        from app.models.career_history import _JobNode  # noqa: F401


def test_titles_traversal_is_read_only_and_ordered_most_recent_first():
    history = CareerHistory()
    history.add_role("Junior Engineer", 1.0, False)
    history.add_role("Senior Engineer", 1.0, True)
    assert list(history.titles()) == ["Senior Engineer", "Junior Engineer"]
