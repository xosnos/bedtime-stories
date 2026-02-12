"""Unit tests for models.py -- RubricScore methods and create_default_failing_score."""

import pytest

from models import RubricScore
from judge import create_default_failing_score


def _make_score(
    safety=5,
    age_fit=5,
    coherence=5,
    engagement=5,
    language_simplicity=5,
):
    """Helper to build a RubricScore with sensible feedback defaults."""
    return RubricScore(
        safety=safety,
        age_fit=age_fit,
        coherence=coherence,
        engagement=engagement,
        language_simplicity=language_simplicity,
        safety_feedback="ok",
        age_fit_feedback="ok",
        coherence_feedback="ok",
        engagement_feedback="ok",
        language_simplicity_feedback="ok",
    )


# ---------- average_score() ----------


def test_average_score_all_fives():
    score = _make_score(5, 5, 5, 5, 5)
    assert score.average_score() == 5.0


def test_average_score_all_ones():
    score = _make_score(1, 1, 1, 1, 1)
    assert score.average_score() == 1.0


def test_average_score_mixed():
    # (5 + 4 + 3 + 2 + 1) / 5 = 3.0
    score = _make_score(5, 4, 3, 2, 1)
    assert score.average_score() == 3.0


def test_average_score_mixed_non_integer():
    # (4 + 4 + 4 + 4 + 3) / 5 = 3.8
    score = _make_score(4, 4, 4, 4, 3)
    assert score.average_score() == pytest.approx(3.8)


def test_average_score_exactly_four():
    # (4 + 4 + 4 + 4 + 4) / 5 = 4.0
    score = _make_score(4, 4, 4, 4, 4)
    assert score.average_score() == 4.0


# ---------- meets_threshold() ----------


def test_meets_threshold_safety_3_fails():
    """Safety=3 should fail even if everything else is perfect."""
    score = _make_score(safety=3, age_fit=5, coherence=5, engagement=5, language_simplicity=5)
    assert score.meets_threshold() is False


def test_meets_threshold_safety_4_passes():
    """Safety=4 with coherence>=4 and average>=4.0 should pass."""
    score = _make_score(safety=4, age_fit=4, coherence=4, engagement=4, language_simplicity=4)
    assert score.meets_threshold() is True


def test_meets_threshold_coherence_3_fails():
    """Coherence=3 should fail even if everything else is perfect."""
    score = _make_score(safety=5, age_fit=5, coherence=3, engagement=5, language_simplicity=5)
    assert score.meets_threshold() is False


def test_meets_threshold_coherence_4_passes():
    """Coherence=4 with safety>=4 and average>=4.0 should pass."""
    score = _make_score(safety=4, age_fit=4, coherence=4, engagement=4, language_simplicity=4)
    assert score.meets_threshold() is True


def test_meets_threshold_average_below_4_fails():
    """Average=3.8 should fail even when safety>=4 and coherence>=4.

    Scores: safety=4, age_fit=3, coherence=4, engagement=4, language_simplicity=4
    Average = (4+3+4+4+4)/5 = 3.8
    """
    score = _make_score(safety=4, age_fit=3, coherence=4, engagement=4, language_simplicity=4)
    assert score.average_score() == pytest.approx(3.8)
    assert score.meets_threshold() is False


def test_meets_threshold_average_exactly_4_passes():
    """Average=4.0 should pass when safety>=4 and coherence>=4.

    Scores: safety=4, age_fit=4, coherence=4, engagement=4, language_simplicity=4
    Average = 4.0
    """
    score = _make_score(safety=4, age_fit=4, coherence=4, engagement=4, language_simplicity=4)
    assert score.average_score() == 4.0
    assert score.meets_threshold() is True


def test_meets_threshold_all_conditions_met():
    """All perfect scores should pass."""
    score = _make_score(5, 5, 5, 5, 5)
    assert score.meets_threshold() is True


def test_meets_threshold_requires_all_three_conditions():
    """Each individual condition is necessary but not sufficient."""
    # Average too low despite safety and coherence being fine
    score1 = _make_score(safety=4, age_fit=1, coherence=4, engagement=1, language_simplicity=5)
    assert score1.safety >= 4
    assert score1.coherence >= 4
    assert score1.average_score() < 4.0
    assert score1.meets_threshold() is False

    # Safety too low despite good average and coherence
    score2 = _make_score(safety=3, age_fit=5, coherence=5, engagement=5, language_simplicity=5)
    assert score2.coherence >= 4
    assert score2.average_score() >= 4.0
    assert score2.safety < 4
    assert score2.meets_threshold() is False

    # Coherence too low despite good average and safety
    score3 = _make_score(safety=5, age_fit=5, coherence=3, engagement=5, language_simplicity=5)
    assert score3.safety >= 4
    assert score3.average_score() >= 4.0
    assert score3.coherence < 4
    assert score3.meets_threshold() is False


# ---------- create_default_failing_score() ----------


def test_create_default_failing_score_all_threes():
    score = create_default_failing_score()
    assert score.safety == 3
    assert score.age_fit == 3
    assert score.coherence == 3
    assert score.engagement == 3
    assert score.language_simplicity == 3


def test_create_default_failing_score_has_feedback():
    score = create_default_failing_score()
    expected = "Judge evaluation failed to parse"
    assert score.safety_feedback == expected
    assert score.age_fit_feedback == expected
    assert score.coherence_feedback == expected
    assert score.engagement_feedback == expected
    assert score.language_simplicity_feedback == expected


def test_create_default_failing_score_does_not_meet_threshold():
    score = create_default_failing_score()
    assert score.meets_threshold() is False
