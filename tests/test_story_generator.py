"""Integration-style tests for the CLI entrypoint in story_generator.py."""

import sys
import os
from unittest.mock import patch

# Ensure project root is on the path so we can import project modules.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import story_generator
from models import StoryBrief, StoryDraft, RubricScore, GenerationResult


def test_story_generator_sample_prompt_with_revision(capsys):
    """Runs the documented sample prompt flow, including one user revision."""
    sample_prompt = (
        "A story about a girl named Alice and her best friend Bob, "
        "who happens to be a cat."
    )
    sample_revision = "Please make the ending gentler and more bedtime-friendly."

    brief = StoryBrief(
        user_request=sample_prompt,
        bedtime_goal="calming",
        age_band=(5, 10),
        target_length=(450, 700),
    )

    initial_score = RubricScore(
        safety=4,
        age_fit=4,
        coherence=4,
        engagement=4,
        language_simplicity=4,
        safety_feedback="Safe.",
        age_fit_feedback="Age-appropriate.",
        coherence_feedback="Clear flow.",
        engagement_feedback="Engaging enough.",
        language_simplicity_feedback="Simple language.",
    )
    initial_draft = StoryDraft(
        title="Alice and Bob's Moonlit Walk",
        story_text="Alice and Bob followed the stars and found their way home.",
        word_count=12,
        rubric_score=initial_score,
    )
    initial_result = GenerationResult(
        final_draft=initial_draft,
        all_attempts=[(initial_draft, initial_score)],
        retry_count=0,
        passed_threshold=True,
    )

    revised_score = RubricScore(
        safety=5,
        age_fit=5,
        coherence=5,
        engagement=4,
        language_simplicity=5,
        safety_feedback="Safe.",
        age_fit_feedback="Great fit.",
        coherence_feedback="Very coherent.",
        engagement_feedback="Warm and engaging.",
        language_simplicity_feedback="Very simple.",
    )
    revised_draft = StoryDraft(
        title="Alice and Bob's Gentle Goodnight",
        story_text="Alice and Bob curled up under the moon and drifted to sleep.",
        word_count=13,
        rubric_score=revised_score,
    )
    revised_result = GenerationResult(
        final_draft=revised_draft,
        all_attempts=[(initial_draft, initial_score), (revised_draft, revised_score)],
        retry_count=1,
        passed_threshold=True,
        revision_used=True,
    )

    with patch("story_generator.normalize_user_request", return_value=brief), \
         patch("story_generator.generate_story_with_judge_loop", return_value=initial_result), \
         patch("story_generator.handle_user_revision", return_value=revised_result) as mock_handle, \
         patch("builtins.input", side_effect=[sample_prompt, "yes", sample_revision]):
        story_generator.main()

    output = capsys.readouterr().out
    assert "Bedtime goal: calming" in output
    assert "TITLE: Alice and Bob's Moonlit Walk" in output
    assert "REVISED TITLE: Alice and Bob's Gentle Goodnight" in output
    assert "Revised Quality Scores:" in output
    assert "Quality threshold met: Yes" in output

    mock_handle.assert_called_once()
    assert mock_handle.call_args.args[1] == sample_revision
