import os
from openai import OpenAI
from dotenv import load_dotenv

# Load variables from .env into the process environment.
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. Add it to .env or export it in your shell."
    )

client = OpenAI(api_key=api_key)

"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

If I were to spend another 2 hours on this project, I would spend roughly an hour on the prompt templates / tailored cateogires to increase engagement in the stories while maintaining safety and constraints. And I'd spend another hour on connecting the project to streamlit to create a simple user interface.
"""

def call_model(prompt: str, max_tokens: int = 3000, temperature: float = 0.1) -> str:
    """Send a prompt to the model and return the generated story text."""
    resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return resp.choices[0].message.content  # type: ignore

example_requests = "A story about a girl named Alice and her best friend Bob, who happens to be a cat."


def main():
    """Run the command-line story generator."""
    from storyteller import normalize_user_request
    from orchestrator import generate_story_with_judge_loop, handle_user_revision

    user_input = input("What kind of story would you like to hear? ")

    brief = normalize_user_request(user_input)
    result = generate_story_with_judge_loop(brief)

    print(f"\n{result.final_draft.title}\n")
    print(result.final_draft.story_text)

    revision_input = input("\nWould you like to request a revision? (yes/no): ")
    if revision_input.lower() in ["yes", "y"]:
        revision_request = input("What would you like to change? ")
        result = handle_user_revision(result, revision_request, brief)

        print(f"\n{result.final_draft.title}\n")
        print(result.final_draft.story_text)

    print("\nSweet dreams!")


if __name__ == "__main__":
    main()