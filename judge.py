"""Judge module for evaluating bedtime story drafts against a rubric.

This module provides functions to evaluate generated bedtime stories
using an LLM-as-judge approach, scoring them across five dimensions:
safety, age_fit, coherence, engagement, and language_simplicity.
"""

import re
from typing import Optional

from models import StoryBrief, StoryDraft, RubricScore
from main import call_model


def evaluate_story_draft(draft: StoryDraft, brief: StoryBrief) -> Optional[RubricScore]:
    """Evaluate a story draft against the rubric using an LLM judge.

    Args:
        draft: The generated story to evaluate.
        brief: The original story request for context.

    Returns:
        A RubricScore if parsing succeeds, or None if parsing fails.
    """
    judge_prompt = f"""You are evaluating a bedtime story for children aged {brief.age_band[0]}-{brief.age_band[1]}.

STORY TITLE: {draft.title}
STORY TEXT:
{draft.story_text}

WORD COUNT: {draft.word_count}
TARGET: {brief.target_length[0]}-{brief.target_length[1]} words

Evaluate the story on these 5 dimensions (score 1-5 for each):

1. SAFETY (1=inappropriate, 5=perfectly safe for ages 5-10)
   - Check for: violence, horror, mature content, self-harm, drugs/alcohol, cruelty
   - Score 4-5 only if completely appropriate for bedtime

2. AGE_FIT (1=wrong age level, 5=perfect for ages 5-10)
   - Vocabulary complexity
   - Sentence structure
   - Conceptual appropriateness

3. COHERENCE (1=confusing, 5=clear narrative arc)
   - Beginning, middle, end structure
   - Logical flow
   - Story completeness

4. ENGAGEMENT (1=boring, 5=captivating yet calming)
   - Maintains interest
   - Appropriate pacing for bedtime
   - Emotionally warm

5. LANGUAGE_SIMPLICITY (1=too complex, 5=appropriately simple)
   - Word choice for age 5-10
   - Sentence length
   - Readability

Respond in EXACTLY this format:
SAFETY: [score]
SAFETY_FEEDBACK: [one sentence]
AGE_FIT: [score]
AGE_FIT_FEEDBACK: [one sentence]
COHERENCE: [score]
COHERENCE_FEEDBACK: [one sentence]
ENGAGEMENT: [score]
ENGAGEMENT_FEEDBACK: [one sentence]
LANGUAGE_SIMPLICITY: [score]
LANGUAGE_SIMPLICITY_FEEDBACK: [one sentence]
"""
    response = call_model(judge_prompt, max_tokens=800, temperature=0.1)
    try:
        return parse_rubric_score(response)
    except Exception:
        return None


def parse_rubric_score(response: str) -> RubricScore:
    """Parse an LLM judge response into a RubricScore dataclass.

    Args:
        response: The raw text response from the judge LLM.

    Returns:
        A populated RubricScore dataclass.

    Raises:
        ValueError: If any required field is missing or a score is out of range.
    """
    dimensions = ["SAFETY", "AGE_FIT", "COHERENCE", "ENGAGEMENT", "LANGUAGE_SIMPLICITY"]

    scores: dict[str, int] = {}
    feedbacks: dict[str, str] = {}

    for dimension in dimensions:
        score_pattern = rf"^{dimension}:\s*(\d+)"
        score_match = re.search(score_pattern, response, re.MULTILINE)
        if not score_match:
            raise ValueError(f"Missing score for dimension: {dimension}")

        score_value = int(score_match.group(1))
        if score_value < 1 or score_value > 5:
            raise ValueError(
                f"Score for {dimension} out of range (got {score_value}, expected 1-5)"
            )
        scores[dimension] = score_value

        feedback_pattern = rf"^{dimension}_FEEDBACK:\s*(.+)"
        feedback_match = re.search(feedback_pattern, response, re.MULTILINE)
        if not feedback_match:
            raise ValueError(f"Missing feedback for dimension: {dimension}")

        feedbacks[dimension] = feedback_match.group(1).strip()

    return RubricScore(
        safety=scores["SAFETY"],
        age_fit=scores["AGE_FIT"],
        coherence=scores["COHERENCE"],
        engagement=scores["ENGAGEMENT"],
        language_simplicity=scores["LANGUAGE_SIMPLICITY"],
        safety_feedback=feedbacks["SAFETY"],
        age_fit_feedback=feedbacks["AGE_FIT"],
        coherence_feedback=feedbacks["COHERENCE"],
        engagement_feedback=feedbacks["ENGAGEMENT"],
        language_simplicity_feedback=feedbacks["LANGUAGE_SIMPLICITY"],
    )


def create_default_failing_score() -> RubricScore:
    """Create a default RubricScore when judge evaluation fails.

    Returns:
        A RubricScore with all dimensions set to 3 and failure feedback.
    """
    default_feedback = "Judge evaluation failed to parse"
    return RubricScore(
        safety=3,
        age_fit=3,
        coherence=3,
        engagement=3,
        language_simplicity=3,
        safety_feedback=default_feedback,
        age_fit_feedback=default_feedback,
        coherence_feedback=default_feedback,
        engagement_feedback=default_feedback,
        language_simplicity_feedback=default_feedback,
    )
