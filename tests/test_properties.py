"""Property-based tests for the bedtime story judge loop.

Uses hypothesis @given decorator with @settings(max_examples=100) to verify
invariants across randomized inputs. LLM calls are mocked for determinism.
"""

import sys
import os
import math
from unittest.mock import patch

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

# Ensure project root is on the path so we can import project modules.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import StoryBrief, StoryDraft, RubricScore, GenerationResult
from judge import parse_rubric_score, create_default_failing_score
from orchestrator import generate_story_with_judge_loop, handle_user_revision
from storyteller import normalize_user_request, generate_story_draft


# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

score_strategy = st.integers(min_value=1, max_value=5)
feedback_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=120,
)

rubric_score_strategy = st.builds(
    RubricScore,
    safety=score_strategy,
    age_fit=score_strategy,
    coherence=score_strategy,
    engagement=score_strategy,
    language_simplicity=score_strategy,
    safety_feedback=feedback_strategy,
    age_fit_feedback=feedback_strategy,
    coherence_feedback=feedback_strategy,
    engagement_feedback=feedback_strategy,
    language_simplicity_feedback=feedback_strategy,
)


def _make_brief() -> StoryBrief:
    """Return a deterministic StoryBrief for tests that need one."""
    return StoryBrief(
        user_request="A story about a sleepy bunny",
        bedtime_goal="calming",
        age_band=(5, 10),
        target_length=(450, 700),
    )


def _build_judge_response(
    safety: int = 5,
    age_fit: int = 5,
    coherence: int = 5,
    engagement: int = 5,
    language_simplicity: int = 5,
) -> str:
    """Build a well-formed judge response string from the given scores."""
    return (
        f"SAFETY: {safety}\n"
        f"SAFETY_FEEDBACK: Safety looks good.\n"
        f"AGE_FIT: {age_fit}\n"
        f"AGE_FIT_FEEDBACK: Age fit is appropriate.\n"
        f"COHERENCE: {coherence}\n"
        f"COHERENCE_FEEDBACK: Story is coherent.\n"
        f"ENGAGEMENT: {engagement}\n"
        f"ENGAGEMENT_FEEDBACK: Story is engaging.\n"
        f"LANGUAGE_SIMPLICITY: {language_simplicity}\n"
        f"LANGUAGE_SIMPLICITY_FEEDBACK: Language is simple enough.\n"
    )


# ===========================================================================
# Property 1: Story Brief Structure
# Feature: bedtime-story-judge-loop, Property 1: Story Brief Structure
# Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
# ===========================================================================

@given(
    user_input=st.text(min_size=1, max_size=300),
    bedtime_goal=st.text(min_size=1, max_size=40),
)
@settings(max_examples=100)
def test_story_brief_structure_invariant(user_input: str, bedtime_goal: str):
    """normalize_user_request() preserves input and sets fixed structural fields."""
    assume("\n" not in bedtime_goal)
    assume(len(bedtime_goal.strip()) > 0)

    with patch("storyteller.call_model", return_value=bedtime_goal):
        brief = normalize_user_request(user_input)

    assert isinstance(brief, StoryBrief)
    assert brief.user_request == user_input
    assert brief.bedtime_goal == bedtime_goal.strip()
    assert len(brief.bedtime_goal) > 0
    assert brief.age_band == (5, 10)
    assert brief.target_length == (450, 700)


# ===========================================================================
# Property 2: Story Draft Structure
# Feature: bedtime-story-judge-loop, Property 2: Story Draft Structure
# Validates: Requirements 2.1, 2.2
# ===========================================================================

@given(
    title=st.text(min_size=1, max_size=80),
    words=st.lists(st.text(min_size=1, max_size=12), min_size=1, max_size=300),
    feedback=st.one_of(st.none(), st.text(min_size=1, max_size=200)),
)
@settings(max_examples=100)
def test_story_draft_structure_invariant(title: str, words: list[str], feedback: str | None):
    """generate_story_draft() returns non-empty title/text and consistent word_count."""
    assume("\n" not in title)
    assume("Title:" not in title)
    assume(len(title.strip()) > 0)
    assume(all("\n" not in w for w in words))

    story_text = " ".join(words)
    model_output = f"Title: {title}\n\n{story_text}"
    brief = _make_brief()

    with patch("storyteller.call_model", return_value=model_output):
        draft = generate_story_draft(brief, feedback=feedback)

    assert isinstance(draft, StoryDraft)
    assert len(draft.title) > 0
    assert len(draft.story_text) > 0
    assert draft.word_count == len(draft.story_text.split())
    assert draft.rubric_score is None


# ===========================================================================
# Property 4: Average Score Calculation
# Feature: bedtime-story-judge-loop, Property 4: Average Score Calculation
# Validates: Requirements 5.4
# ===========================================================================

@given(data=rubric_score_strategy)
@settings(max_examples=100)
def test_average_score_calculation(data: RubricScore):
    """average_score() must equal (sum of 5 dimensions) / 5.0."""
    expected = (
        data.safety + data.age_fit + data.coherence +
        data.engagement + data.language_simplicity
    ) / 5.0
    assert math.isclose(data.average_score(), expected, rel_tol=1e-9)


# ===========================================================================
# Property 5: Threshold Logic Correctness
# Feature: bedtime-story-judge-loop, Property 5: Threshold Logic Correctness
# Validates: Requirements 5.1, 5.2, 5.3, 5.5
# ===========================================================================

@given(data=rubric_score_strategy)
@settings(max_examples=100)
def test_threshold_logic_correctness(data: RubricScore):
    """meets_threshold() returns True iff safety>=4 AND coherence>=4 AND average>=4.0."""
    expected = (
        data.safety >= 4
        and data.coherence >= 4
        and data.average_score() >= 4.0
    )
    assert data.meets_threshold() == expected


# ===========================================================================
# Property 3: Rubric Score Structure
# Feature: bedtime-story-judge-loop, Property 3: Rubric Score Structure
# Validates: Requirements 3.1, 3.2, 3.3
# ===========================================================================

@given(
    safety=score_strategy,
    age_fit=score_strategy,
    coherence=score_strategy,
    engagement=score_strategy,
    language_simplicity=score_strategy,
    safety_fb=feedback_strategy,
    age_fit_fb=feedback_strategy,
    coherence_fb=feedback_strategy,
    engagement_fb=feedback_strategy,
    lang_fb=feedback_strategy,
)
@settings(max_examples=100)
def test_rubric_score_structure(
    safety, age_fit, coherence, engagement, language_simplicity,
    safety_fb, age_fit_fb, coherence_fb, engagement_fb, lang_fb,
):
    """parse_rubric_score() returns scores in [1,5] and non-empty feedback."""
    assume("\n" not in safety_fb)
    assume("\n" not in age_fit_fb)
    assume("\n" not in coherence_fb)
    assume("\n" not in engagement_fb)
    assume("\n" not in lang_fb)

    response = (
        f"SAFETY: {safety}\n"
        f"SAFETY_FEEDBACK: {safety_fb}\n"
        f"AGE_FIT: {age_fit}\n"
        f"AGE_FIT_FEEDBACK: {age_fit_fb}\n"
        f"COHERENCE: {coherence}\n"
        f"COHERENCE_FEEDBACK: {coherence_fb}\n"
        f"ENGAGEMENT: {engagement}\n"
        f"ENGAGEMENT_FEEDBACK: {engagement_fb}\n"
        f"LANGUAGE_SIMPLICITY: {language_simplicity}\n"
        f"LANGUAGE_SIMPLICITY_FEEDBACK: {lang_fb}\n"
    )

    result = parse_rubric_score(response)

    for dim_name, val in [
        ("safety", result.safety),
        ("age_fit", result.age_fit),
        ("coherence", result.coherence),
        ("engagement", result.engagement),
        ("language_simplicity", result.language_simplicity),
    ]:
        assert 1 <= val <= 5, f"{dim_name} score {val} not in [1,5]"

    for dim_name, fb in [
        ("safety_feedback", result.safety_feedback),
        ("age_fit_feedback", result.age_fit_feedback),
        ("coherence_feedback", result.coherence_feedback),
        ("engagement_feedback", result.engagement_feedback),
        ("language_simplicity_feedback", result.language_simplicity_feedback),
    ]:
        assert len(fb) > 0, f"{dim_name} feedback is empty"


# ===========================================================================
# Property 6: Bounded Retry Invariant
# Feature: bedtime-story-judge-loop, Property 6: Bounded Retry Invariant
# Validates: Requirements 4.1
# ===========================================================================

@given(max_attempts=st.integers(min_value=1, max_value=6))
@settings(max_examples=100)
def test_bounded_retry_invariant(max_attempts: int):
    """retry_count never exceeds max_attempts-1, all_attempts length bounded."""
    brief = _make_brief()
    failing_judge = _build_judge_response(
        safety=2, age_fit=2, coherence=2, engagement=2, language_simplicity=2
    )

    def mock_call_model(prompt, max_tokens=3000, temperature=0.1):
        if "evaluating a bedtime story" in prompt.lower() or "Evaluate the story" in prompt:
            return failing_judge
        return "Title: Sleepy Bunny\n\nOnce upon a time a bunny went to sleep."

    with patch("main.call_model", side_effect=mock_call_model), \
         patch("storyteller.call_model", side_effect=mock_call_model), \
         patch("judge.call_model", side_effect=mock_call_model), \
         patch("orchestrator.call_model", side_effect=mock_call_model):
        result = generate_story_with_judge_loop(brief, max_attempts=max_attempts)

    assert 0 <= result.retry_count <= max_attempts - 1
    assert len(result.all_attempts) <= max_attempts


# ===========================================================================
# Property 7: Early Exit on Pass
# Feature: bedtime-story-judge-loop, Property 7: Early Exit on Pass
# Validates: Requirements 4.3
# ===========================================================================

@given(
    safety=st.integers(min_value=4, max_value=5),
    coherence=st.integers(min_value=4, max_value=5),
    engagement=st.integers(min_value=4, max_value=5),
    language_simplicity=st.integers(min_value=4, max_value=5),
)
@settings(max_examples=100)
def test_early_exit_on_pass(safety, coherence, engagement, language_simplicity):
    """When the judge returns passing scores, the loop exits on the first attempt."""
    age_fit = 5
    passing_judge = _build_judge_response(
        safety=safety, age_fit=age_fit, coherence=coherence,
        engagement=engagement, language_simplicity=language_simplicity,
    )
    brief = _make_brief()

    def mock_call_model(prompt, max_tokens=3000, temperature=0.1):
        if "evaluating a bedtime story" in prompt.lower() or "Evaluate the story" in prompt:
            return passing_judge
        return "Title: Sleepy Bunny\n\nOnce upon a time a bunny went to sleep."

    with patch("main.call_model", side_effect=mock_call_model), \
         patch("storyteller.call_model", side_effect=mock_call_model), \
         patch("judge.call_model", side_effect=mock_call_model), \
         patch("orchestrator.call_model", side_effect=mock_call_model):
        result = generate_story_with_judge_loop(brief, max_attempts=3)

    assert result.passed_threshold is True
    assert result.retry_count == 0
    assert len(result.all_attempts) == 1


# ===========================================================================
# Property 8: Best Draft Selection
# Feature: bedtime-story-judge-loop, Property 8: Best Draft Selection
# Validates: Requirements 4.5
# ===========================================================================

@given(
    s1=st.integers(min_value=1, max_value=3),
    s2=st.integers(min_value=1, max_value=3),
    s3=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100)
def test_best_draft_selection(s1, s2, s3):
    """When all attempts fail threshold, the returned draft has the highest average."""
    judges = [
        _build_judge_response(safety=s1, age_fit=s1, coherence=s1, engagement=s1, language_simplicity=s1),
        _build_judge_response(safety=s2, age_fit=s2, coherence=s2, engagement=s2, language_simplicity=s2),
        _build_judge_response(safety=s3, age_fit=s3, coherence=s3, engagement=s3, language_simplicity=s3),
    ]
    call_idx = {"storyteller": 0, "judge": 0}

    def mock_call_model(prompt, max_tokens=3000, temperature=0.1):
        if "evaluating a bedtime story" in prompt.lower() or "Evaluate the story" in prompt:
            idx = min(call_idx["judge"], len(judges) - 1)
            resp = judges[idx]
            call_idx["judge"] += 1
            return resp
        idx = min(call_idx["storyteller"], 2)
        call_idx["storyteller"] += 1
        return f"Title: Story {idx}\n\nOnce upon a time story number {idx}."

    brief = _make_brief()

    with patch("main.call_model", side_effect=mock_call_model), \
         patch("storyteller.call_model", side_effect=mock_call_model), \
         patch("judge.call_model", side_effect=mock_call_model), \
         patch("orchestrator.call_model", side_effect=mock_call_model):
        result = generate_story_with_judge_loop(brief, max_attempts=3)

    assert result.passed_threshold is False

    best_avg_in_attempts = max(
        score.average_score() for _, score in result.all_attempts
    )
    final_avg = result.final_draft.rubric_score.average_score()
    assert math.isclose(final_avg, best_avg_in_attempts, rel_tol=1e-9)


# ===========================================================================
# Property 9: Disclaimer on Failure
# Feature: bedtime-story-judge-loop, Property 9: Disclaimer on Failure
# Validates: Requirements 4.6, 9.4
# ===========================================================================

@given(
    safety=st.integers(min_value=1, max_value=3),
    coherence=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=100)
def test_disclaimer_on_failure(safety, coherence):
    """When passed_threshold is False, disclaimer must be non-None."""
    failing_judge = _build_judge_response(
        safety=safety, age_fit=2, coherence=coherence, engagement=2, language_simplicity=2,
    )
    brief = _make_brief()

    def mock_call_model(prompt, max_tokens=3000, temperature=0.1):
        if "evaluating a bedtime story" in prompt.lower() or "Evaluate the story" in prompt:
            return failing_judge
        return "Title: Sleepy Bunny\n\nOnce upon a time a bunny went to sleep."

    with patch("main.call_model", side_effect=mock_call_model), \
         patch("storyteller.call_model", side_effect=mock_call_model), \
         patch("judge.call_model", side_effect=mock_call_model), \
         patch("orchestrator.call_model", side_effect=mock_call_model):
        result = generate_story_with_judge_loop(brief, max_attempts=3)

    assert result.passed_threshold is False
    assert result.disclaimer is not None
    assert len(result.disclaimer) > 0


# ===========================================================================
# Property 10: Generation Result Completeness
# Feature: bedtime-story-judge-loop, Property 10: Generation Result Completeness
# Validates: Requirements 4.7, 9.1, 9.2, 9.3, 9.5
# ===========================================================================

@given(max_attempts=st.integers(min_value=1, max_value=5))
@settings(max_examples=100)
def test_generation_result_completeness(max_attempts):
    """Result has non-empty title/text, non-None rubric_score, valid retry_count."""
    passing_judge = _build_judge_response(
        safety=5, age_fit=5, coherence=5, engagement=5, language_simplicity=5
    )
    brief = _make_brief()

    def mock_call_model(prompt, max_tokens=3000, temperature=0.1):
        if "evaluating a bedtime story" in prompt.lower() or "Evaluate the story" in prompt:
            return passing_judge
        return "Title: Sleepy Bunny\n\nOnce upon a time a bunny went to sleep soundly."

    with patch("main.call_model", side_effect=mock_call_model), \
         patch("storyteller.call_model", side_effect=mock_call_model), \
         patch("judge.call_model", side_effect=mock_call_model), \
         patch("orchestrator.call_model", side_effect=mock_call_model):
        result = generate_story_with_judge_loop(brief, max_attempts=max_attempts)

    assert len(result.final_draft.title) > 0
    assert len(result.final_draft.story_text) > 0
    assert result.final_draft.rubric_score is not None
    assert 0 <= result.retry_count <= max_attempts - 1
    assert 1 <= len(result.all_attempts) <= max_attempts

    for i, (draft, score) in enumerate(result.all_attempts):
        assert isinstance(draft, StoryDraft), f"Attempt {i} draft is not StoryDraft"
        assert isinstance(score, RubricScore), f"Attempt {i} score is not RubricScore"


# ===========================================================================
# Property 11: Parse Failure Handling
# Feature: bedtime-story-judge-loop, Property 11: Parse Failure Handling
# Validates: Requirements 7.1, 7.2, 7.3, 7.4
# ===========================================================================

@given(max_attempts=st.integers(min_value=1, max_value=4))
@settings(max_examples=100)
def test_parse_failure_handling(max_attempts):
    """When the judge returns unparseable responses, fallback to default scores."""
    brief = _make_brief()

    def mock_call_model(prompt, max_tokens=3000, temperature=0.1):
        if "evaluating a bedtime story" in prompt.lower() or "Evaluate the story" in prompt:
            return "This is not a valid rubric response at all."
        return "Title: Sleepy Bunny\n\nOnce upon a time a bunny went to sleep."

    with patch("main.call_model", side_effect=mock_call_model), \
         patch("storyteller.call_model", side_effect=mock_call_model), \
         patch("judge.call_model", side_effect=mock_call_model), \
         patch("orchestrator.call_model", side_effect=mock_call_model):
        result = generate_story_with_judge_loop(brief, max_attempts=max_attempts)

    assert result.judge_parse_failures >= 1
    assert result.judge_parse_failures <= max_attempts

    default = create_default_failing_score()
    for _, score in result.all_attempts:
        assert score.safety == default.safety
        assert score.average_score() == default.average_score()

    assert result.passed_threshold is False


# ===========================================================================
# Property 12: Safety Invariant
# Feature: bedtime-story-judge-loop, Property 12: Safety Invariant
# Validates: Requirements 8.5
# ===========================================================================

@given(
    safety=st.integers(min_value=4, max_value=5),
    age_fit=st.integers(min_value=4, max_value=5),
    coherence=st.integers(min_value=4, max_value=5),
    engagement=st.integers(min_value=4, max_value=5),
    language_simplicity=st.integers(min_value=4, max_value=5),
)
@settings(max_examples=100)
def test_safety_invariant(safety, age_fit, coherence, engagement, language_simplicity):
    """When passed_threshold is True, safety must be >= 4."""
    passing_judge = _build_judge_response(
        safety=safety, age_fit=age_fit, coherence=coherence,
        engagement=engagement, language_simplicity=language_simplicity,
    )
    brief = _make_brief()

    def mock_call_model(prompt, max_tokens=3000, temperature=0.1):
        if "evaluating a bedtime story" in prompt.lower() or "Evaluate the story" in prompt:
            return passing_judge
        return "Title: Sleepy Bunny\n\nOnce upon a time a bunny went to sleep."

    with patch("main.call_model", side_effect=mock_call_model), \
         patch("storyteller.call_model", side_effect=mock_call_model), \
         patch("judge.call_model", side_effect=mock_call_model), \
         patch("orchestrator.call_model", side_effect=mock_call_model):
        result = generate_story_with_judge_loop(brief, max_attempts=3)

    if result.passed_threshold:
        assert result.final_draft.rubric_score.safety >= 4


# ===========================================================================
# Property 13: Revision Re-evaluation
# Feature: bedtime-story-judge-loop, Property 13: Revision Re-evaluation
# Validates: Requirements 6.3, 6.4, 6.5, 6.7
# ===========================================================================

@given(data=rubric_score_strategy)
@settings(max_examples=100)
def test_revision_re_evaluation(data: RubricScore):
    """handle_user_revision() re-evaluates revised text and updates result metadata."""
    previous_score = create_default_failing_score()
    previous_draft = StoryDraft(
        title="Original",
        story_text="A calm story about bedtime.",
        word_count=5,
        rubric_score=previous_score,
    )
    previous_result = GenerationResult(
        final_draft=previous_draft,
        all_attempts=[(previous_draft, previous_score)],
        retry_count=0,
        passed_threshold=False,
        disclaimer="Note: fallback",
        judge_parse_failures=0,
        revision_used=False,
    )

    revised_output = "Title: Revised Story\n\nA gentler revised bedtime tale."
    brief = _make_brief()

    with patch("orchestrator.call_model", return_value=revised_output), \
         patch("orchestrator.evaluate_story_draft", return_value=data):
        revised_result = handle_user_revision(
            previous_result,
            revision_request="Please make it calmer and shorter.",
            brief=brief,
        )

    assert revised_result.revision_used is True
    assert len(revised_result.all_attempts) == len(previous_result.all_attempts) + 1
    assert revised_result.final_draft.rubric_score == data
    assert revised_result.all_attempts[-1][1] == data
    assert revised_result.passed_threshold == data.meets_threshold()
    assert revised_result.retry_count == previous_result.retry_count + 1
