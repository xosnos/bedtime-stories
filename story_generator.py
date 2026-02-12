"""Enhanced command-line story generator with judge loop.

Main entry point for the bedtime story generation system. Prompts the user
for a story request, generates and evaluates stories through the judge loop,
and optionally supports one user revision.
"""

from storyteller import normalize_user_request
from orchestrator import generate_story_with_judge_loop, handle_user_revision


def main():
    """Run the enhanced command-line story generator."""
    print("=== Bedtime Story Generator with Quality Judge ===\n")

    # Get user input
    user_input = input("What kind of story would you like to hear? ")

    # Normalize to story brief
    print("\nPreparing your story request...")
    brief = normalize_user_request(user_input)
    print(f"Bedtime goal: {brief.bedtime_goal}")
    print(f"Target audience: Ages {brief.age_band[0]}-{brief.age_band[1]}")
    print(f"Target length: {brief.target_length[0]}-{brief.target_length[1]} words\n")

    # Generate story with judge loop
    print("Generating and evaluating story (this may take a moment)...\n")
    result = generate_story_with_judge_loop(brief)

    # Display result
    print("=" * 60)
    print(f"TITLE: {result.final_draft.title}")
    print("=" * 60)
    print(result.final_draft.story_text)
    print("=" * 60)
    print(f"\nWord count: {result.final_draft.word_count}")
    print(f"Attempts: {result.retry_count + 1}")
    print(f"Quality threshold met: {'Yes' if result.passed_threshold else 'No'}")
    if result.judge_parse_failures > 0:
        print(f"Judge parse failures: {result.judge_parse_failures}")

    if result.disclaimer:
        print(f"\n{result.disclaimer}")

    # Display scores
    score = result.final_draft.rubric_score
    print(f"\nQuality Scores:")
    print(f"  Safety: {score.safety}/5 - {score.safety_feedback}")
    print(f"  Age Fit: {score.age_fit}/5 - {score.age_fit_feedback}")
    print(f"  Coherence: {score.coherence}/5 - {score.coherence_feedback}")
    print(f"  Engagement: {score.engagement}/5 - {score.engagement_feedback}")
    print(f"  Language Simplicity: {score.language_simplicity}/5 - {score.language_simplicity_feedback}")
    print(f"  Average: {score.average_score():.1f}/5")

    # Offer revision
    print("\n" + "=" * 60)
    revision_input = input("\nWould you like to request a revision? (yes/no): ")

    if revision_input.lower() in ["yes", "y"]:
        revision_request = input("What would you like to change? ")
        print("\nGenerating revised story...\n")
        result = handle_user_revision(result, revision_request, brief)

        # Display revised result
        print("=" * 60)
        print(f"REVISED TITLE: {result.final_draft.title}")
        print("=" * 60)
        print(result.final_draft.story_text)
        print("=" * 60)
        print(f"\nWord count: {result.final_draft.word_count}")
        print(f"Quality threshold met: {'Yes' if result.passed_threshold else 'No'}")
        if result.judge_parse_failures > 0:
            print(f"Judge parse failures: {result.judge_parse_failures}")

        if result.disclaimer:
            print(f"\n{result.disclaimer}")

        score = result.final_draft.rubric_score
        print(f"\nRevised Quality Scores:")
        print(f"  Safety: {score.safety}/5")
        print(f"  Age Fit: {score.age_fit}/5")
        print(f"  Coherence: {score.coherence}/5")
        print(f"  Engagement: {score.engagement}/5")
        print(f"  Language Simplicity: {score.language_simplicity}/5")
        print(f"  Average: {score.average_score():.1f}/5")

    print("\nThank you for using Bedtime Story Generator! Sweet dreams!")


if __name__ == "__main__":
    main()
