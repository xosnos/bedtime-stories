"""Orchestrator module for the story generation workflow.

Manages the bounded retry loop, threshold checking, feedback formatting,
and user revision workflow.
"""

import logging
from typing import Optional

from models import StoryBrief, StoryDraft, RubricScore, GenerationResult
from storyteller import generate_story_draft
from judge import evaluate_story_draft, create_default_failing_score
from main import call_model

logger = logging.getLogger(__name__)

MAX_RETRY_ATTEMPTS = 3


def generate_story_with_judge_loop(brief: StoryBrief, max_attempts: int = 3) -> GenerationResult:
    """Run the story generation loop with judge evaluation and bounded retries.

    Args:
        brief: Structured story request.
        max_attempts: Maximum generation attempts (capped at 3 per Req 4.1).

    Returns:
        GenerationResult with final story and metadata.
    """
    max_attempts = min(max_attempts, MAX_RETRY_ATTEMPTS)

    all_attempts = []
    judge_parse_failures = 0
    best_draft = None
    best_score = None
    best_avg = 0.0
    latest_score = None

    for attempt in range(max_attempts):
        # Generate draft (with feedback from most recent failed attempt if available)
        feedback = None
        if attempt > 0 and latest_score:
            feedback = format_judge_feedback(latest_score)

        draft = generate_story_draft(brief, feedback)

        # Evaluate draft
        rubric_score = evaluate_story_draft(draft, brief)

        # Handle parse failure with retry
        if rubric_score is None:
            rubric_score = evaluate_story_draft(draft, brief)
            if rubric_score is None:
                logger.warning("Judge parse failure: both parse attempts failed on attempt %d, using default scores", attempt + 1)
                rubric_score = create_default_failing_score()
                judge_parse_failures += 1

        draft.rubric_score = rubric_score
        all_attempts.append((draft, rubric_score))
        latest_score = rubric_score

        # Track best draft
        avg = rubric_score.average_score()
        if avg > best_avg:
            best_draft = draft
            best_score = rubric_score
            best_avg = avg

        # Check if threshold met
        if rubric_score.meets_threshold():
            return GenerationResult(
                final_draft=draft,
                all_attempts=all_attempts,
                retry_count=attempt,
                passed_threshold=True,
                judge_parse_failures=judge_parse_failures,
            )

    # All attempts exhausted, return best with disclaimer
    disclaimer = (
        "Note: This story did not fully meet all quality thresholds "
        "after 3 attempts. This is the best version generated."
    )

    return GenerationResult(
        final_draft=best_draft,
        all_attempts=all_attempts,
        retry_count=max_attempts - 1,
        passed_threshold=False,
        disclaimer=disclaimer,
        judge_parse_failures=judge_parse_failures,
    )


def format_judge_feedback(score: RubricScore) -> str:
    """Format rubric score into actionable feedback for the storyteller.

    Only includes dimensions with score < 4.

    Args:
        score: The rubric score to format.

    Returns:
        Formatted feedback string.
    """
    feedback_parts = []

    if score.safety < 4:
        feedback_parts.append(f"SAFETY (score {score.safety}): {score.safety_feedback}")
    if score.age_fit < 4:
        feedback_parts.append(f"AGE_FIT (score {score.age_fit}): {score.age_fit_feedback}")
    if score.coherence < 4:
        feedback_parts.append(f"COHERENCE (score {score.coherence}): {score.coherence_feedback}")
    if score.engagement < 4:
        feedback_parts.append(f"ENGAGEMENT (score {score.engagement}): {score.engagement_feedback}")
    if score.language_simplicity < 4:
        feedback_parts.append(
            f"LANGUAGE_SIMPLICITY (score {score.language_simplicity}): "
            f"{score.language_simplicity_feedback}"
        )

    return "\n".join(feedback_parts)


def handle_user_revision(
    result: GenerationResult, revision_request: str, brief: StoryBrief
) -> GenerationResult:
    """Process a user-directed revision with full safety re-check.

    Args:
        result: Previous generation result.
        revision_request: User's revision instructions.
        brief: Original story brief.

    Returns:
        New GenerationResult with revised story.

    Raises:
        ValueError: If a revision has already been used this session (Req 6.6).
    """
    if result.revision_used:
        raise ValueError("Only one revision per session is allowed (Req 6.6)")
    revision_prompt = f"""You are revising a bedtime story for children aged {brief.age_band[0]}-{brief.age_band[1]}.

ORIGINAL STORY:
Title: {result.final_draft.title}
{result.final_draft.story_text}

USER REVISION REQUEST:
{revision_request}

IMPORTANT: Maintain ALL safety requirements:
- NO graphic violence, intense horror, or scary content
- NO sexual or mature content
- NO self-harm, drugs/alcohol, or cruelty
- Keep emotionally warm, calming bedtime tone
- Use age-appropriate vocabulary

If the user's request would violate safety requirements, politely decline and keep the story safe.

Generate the revised story with the same format:
Title: [Story Title]

[Story text here...]
"""

    response = call_model(revision_prompt, max_tokens=1500, temperature=0.8)

    # Parse revised draft
    lines = response.strip().split("\n")
    title = lines[0].replace("Title:", "").strip()
    story_text = "\n".join(lines[1:]).strip()
    word_count = len(story_text.split())

    revised_draft = StoryDraft(title=title, story_text=story_text, word_count=word_count)

    # Re-evaluate with judge
    rubric_score = evaluate_story_draft(revised_draft, brief)
    judge_parse_failures = 0

    if rubric_score is None:
        rubric_score = evaluate_story_draft(revised_draft, brief)
        if rubric_score is None:
            logger.warning("Judge parse failure: both parse attempts failed during revision, using default scores")
            rubric_score = create_default_failing_score()
            judge_parse_failures = 1

    revised_draft.rubric_score = rubric_score

    # Create new result
    new_attempts = result.all_attempts + [(revised_draft, rubric_score)]
    passed = rubric_score.meets_threshold()
    disclaimer = None if passed else "Note: The revised story did not meet all quality thresholds."

    return GenerationResult(
        final_draft=revised_draft,
        all_attempts=new_attempts,
        retry_count=result.retry_count + 1,
        passed_threshold=passed,
        disclaimer=disclaimer,
        judge_parse_failures=result.judge_parse_failures + judge_parse_failures,
        revision_used=True,
    )
