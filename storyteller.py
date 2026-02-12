"""Storyteller module for bedtime story generation.

Provides functions to normalize user requests into structured StoryBriefs
and generate age-appropriate bedtime story drafts using the language model.
"""

from typing import Optional

from models import StoryBrief, StoryDraft
from main import call_model


def normalize_user_request(user_input: str) -> StoryBrief:
    """Normalize a free-form user request into a structured StoryBrief.

    Args:
        user_input: Raw user request describing the desired story.

    Returns:
        A StoryBrief with inferred bedtime_goal, fixed age_band (5, 10),
        and fixed target_length (450, 700).
    """
    normalization_prompt = f"""Given this bedtime story request, identify an appropriate bedtime goal (e.g., "calming", "comforting", "gentle adventure").

User request: {user_input}

Respond with ONLY the bedtime goal as a short phrase (2-4 words)."""

    bedtime_goal = call_model(normalization_prompt, max_tokens=50, temperature=0.3)

    return StoryBrief(
        user_request=user_input,
        bedtime_goal=bedtime_goal.strip(),
        age_band=(5, 10),
        target_length=(450, 700),
    )


def generate_story_draft(
    brief: StoryBrief, feedback: Optional[str] = None
) -> StoryDraft:
    """Generate a bedtime story draft from a structured StoryBrief.

    Args:
        brief: Structured story request with user_request, bedtime_goal,
               age_band, and target_length.
        feedback: Optional judge feedback from a prior attempt.

    Returns:
        A StoryDraft containing the parsed title, story text, and word count.
    """
    safety_constraints = """
STRICT SAFETY REQUIREMENTS (Ages 5-10):
- NO graphic violence, intense horror, or scary content
- NO sexual or mature content of any kind
- NO self-harm, drug/alcohol misuse, or sustained cruelty
- Maintain emotionally warm, calming bedtime tone
- Use age-appropriate vocabulary and simple sentence structures
"""

    feedback_section = ""
    if feedback:
        feedback_section = f"""
PREVIOUS ATTEMPT FEEDBACK:
{feedback}

Please address the feedback above while maintaining all safety requirements.
"""

    storyteller_prompt = f"""You are a bedtime storyteller for children aged {brief.age_band[0]}-{brief.age_band[1]}.

{safety_constraints}

USER REQUEST: {brief.user_request}
BEDTIME GOAL: {brief.bedtime_goal}
TARGET LENGTH: {brief.target_length[0]}-{brief.target_length[1]} words

{feedback_section}

Generate a bedtime story with:
1. A clear title on the first line
2. A complete story with beginning, middle, and end
3. Age-appropriate vocabulary and sentence complexity
4. Warm, calming tone suitable for bedtime
5. Word count between {brief.target_length[0]}-{brief.target_length[1]} words

Format:
Title: [Story Title]

[Story text here...]
"""

    response = call_model(storyteller_prompt, max_tokens=1500, temperature=0.8)

    lines = response.strip().split("\n")
    title = lines[0].replace("Title:", "").strip()
    story_text = "\n".join(lines[1:]).strip()
    word_count = len(story_text.split())

    return StoryDraft(title=title, story_text=story_text, word_count=word_count)
