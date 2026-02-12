"""Unit tests for parse_rubric_score() and format_judge_feedback()."""

import pytest

from models import RubricScore
from judge import parse_rubric_score
from orchestrator import format_judge_feedback


# ---------- helpers ----------

VALID_RESPONSE = """\
SAFETY: 5
SAFETY_FEEDBACK: Perfectly safe for children.
AGE_FIT: 4
AGE_FIT_FEEDBACK: Appropriate vocabulary for ages 5-10.
COHERENCE: 5
COHERENCE_FEEDBACK: Clear beginning, middle, and end.
ENGAGEMENT: 4
ENGAGEMENT_FEEDBACK: Warm and calming story.
LANGUAGE_SIMPLICITY: 3
LANGUAGE_SIMPLICITY_FEEDBACK: A few words could be simpler."""


def _make_score(
    safety=5,
    age_fit=5,
    coherence=5,
    engagement=5,
    language_simplicity=5,
    safety_fb="ok",
    age_fit_fb="ok",
    coherence_fb="ok",
    engagement_fb="ok",
    language_simplicity_fb="ok",
):
    return RubricScore(
        safety=safety,
        age_fit=age_fit,
        coherence=coherence,
        engagement=engagement,
        language_simplicity=language_simplicity,
        safety_feedback=safety_fb,
        age_fit_feedback=age_fit_fb,
        coherence_feedback=coherence_fb,
        engagement_feedback=engagement_fb,
        language_simplicity_feedback=language_simplicity_fb,
    )


# ---------- parse_rubric_score() with valid input ----------


def test_parse_rubric_score_valid_response():
    score = parse_rubric_score(VALID_RESPONSE)
    assert isinstance(score, RubricScore)
    assert score.safety == 5
    assert score.age_fit == 4
    assert score.coherence == 5
    assert score.engagement == 4
    assert score.language_simplicity == 3


def test_parse_rubric_score_valid_feedback():
    score = parse_rubric_score(VALID_RESPONSE)
    assert score.safety_feedback == "Perfectly safe for children."
    assert score.age_fit_feedback == "Appropriate vocabulary for ages 5-10."
    assert score.coherence_feedback == "Clear beginning, middle, and end."
    assert score.engagement_feedback == "Warm and calming story."
    assert score.language_simplicity_feedback == "A few words could be simpler."


# ---------- parse_rubric_score() raises ValueError on missing fields ----------


def test_parse_rubric_score_missing_score_field():
    """Removing the COHERENCE line should raise ValueError."""
    bad_response = "\n".join(
        line for line in VALID_RESPONSE.splitlines()
        if not line.startswith("COHERENCE:")
    )
    with pytest.raises(ValueError, match="Missing score for dimension: COHERENCE"):
        parse_rubric_score(bad_response)


def test_parse_rubric_score_missing_feedback_field():
    """Removing the ENGAGEMENT_FEEDBACK line should raise ValueError."""
    bad_response = "\n".join(
        line for line in VALID_RESPONSE.splitlines()
        if not line.startswith("ENGAGEMENT_FEEDBACK:")
    )
    with pytest.raises(ValueError, match="Missing feedback for dimension: ENGAGEMENT"):
        parse_rubric_score(bad_response)


def test_parse_rubric_score_missing_first_dimension():
    """Removing the SAFETY line should raise ValueError."""
    bad_response = "\n".join(
        line for line in VALID_RESPONSE.splitlines()
        if not line.startswith("SAFETY:")
    )
    with pytest.raises(ValueError, match="Missing score for dimension: SAFETY"):
        parse_rubric_score(bad_response)


def test_parse_rubric_score_empty_string():
    with pytest.raises(ValueError):
        parse_rubric_score("")


# ---------- parse_rubric_score() raises ValueError on out-of-range scores ----------


def test_parse_rubric_score_score_too_high():
    bad_response = VALID_RESPONSE.replace("SAFETY: 5", "SAFETY: 6")
    with pytest.raises(ValueError, match="out of range"):
        parse_rubric_score(bad_response)


def test_parse_rubric_score_score_too_low():
    bad_response = VALID_RESPONSE.replace("SAFETY: 5", "SAFETY: 0")
    with pytest.raises(ValueError, match="out of range"):
        parse_rubric_score(bad_response)


def test_parse_rubric_score_score_negative():
    bad_response = VALID_RESPONSE.replace("ENGAGEMENT: 4", "ENGAGEMENT: -1")
    # -1 won't match \d+ pattern, so it should raise missing score
    with pytest.raises(ValueError, match="Missing score for dimension: ENGAGEMENT"):
        parse_rubric_score(bad_response)


# ---------- format_judge_feedback() with all scores >= 4 ----------


def test_format_judge_feedback_all_passing():
    """When every dimension is >= 4, feedback should be empty."""
    score = _make_score(
        safety=4, age_fit=4, coherence=5, engagement=4, language_simplicity=5,
    )
    result = format_judge_feedback(score)
    assert result == ""


def test_format_judge_feedback_all_fives():
    """Perfect scores produce empty feedback."""
    score = _make_score(5, 5, 5, 5, 5)
    assert format_judge_feedback(score) == ""


# ---------- format_judge_feedback() with mixed scores ----------


def test_format_judge_feedback_mixed_scores():
    """Only dimensions with score < 4 should appear in feedback."""
    score = _make_score(
        safety=5,
        age_fit=3,
        coherence=4,
        engagement=2,
        language_simplicity=5,
        age_fit_fb="Vocabulary is too advanced.",
        engagement_fb="Story is not engaging enough.",
    )
    result = format_judge_feedback(score)

    assert "AGE_FIT (score 3): Vocabulary is too advanced." in result
    assert "ENGAGEMENT (score 2): Story is not engaging enough." in result

    assert "SAFETY" not in result
    assert "COHERENCE" not in result
    assert "LANGUAGE_SIMPLICITY" not in result


def test_format_judge_feedback_single_failing_dimension():
    """Only one dimension below threshold."""
    score = _make_score(
        safety=4,
        age_fit=4,
        coherence=4,
        engagement=4,
        language_simplicity=3,
        language_simplicity_fb="Sentences are too long.",
    )
    result = format_judge_feedback(score)
    assert result == "LANGUAGE_SIMPLICITY (score 3): Sentences are too long."


# ---------- format_judge_feedback() with all scores < 4 ----------


def test_format_judge_feedback_all_failing():
    """When every dimension is < 4, all should appear in feedback."""
    score = _make_score(
        safety=1,
        age_fit=2,
        coherence=3,
        engagement=1,
        language_simplicity=2,
        safety_fb="Contains violence.",
        age_fit_fb="Too complex.",
        coherence_fb="No clear structure.",
        engagement_fb="Boring.",
        language_simplicity_fb="Words too hard.",
    )
    result = format_judge_feedback(score)
    lines = result.strip().split("\n")

    assert len(lines) == 5
    assert "SAFETY (score 1): Contains violence." in result
    assert "AGE_FIT (score 2): Too complex." in result
    assert "COHERENCE (score 3): No clear structure." in result
    assert "ENGAGEMENT (score 1): Boring." in result
    assert "LANGUAGE_SIMPLICITY (score 2): Words too hard." in result


def test_format_judge_feedback_preserves_order():
    """Feedback lines should appear in dimension order."""
    score = _make_score(
        safety=2,
        age_fit=1,
        coherence=3,
        engagement=2,
        language_simplicity=1,
        safety_fb="s",
        age_fit_fb="a",
        coherence_fb="c",
        engagement_fb="e",
        language_simplicity_fb="l",
    )
    result = format_judge_feedback(score)
    lines = result.strip().split("\n")

    assert lines[0].startswith("SAFETY")
    assert lines[1].startswith("AGE_FIT")
    assert lines[2].startswith("COHERENCE")
    assert lines[3].startswith("ENGAGEMENT")
    assert lines[4].startswith("LANGUAGE_SIMPLICITY")
