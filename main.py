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
    user_input = input("What kind of story do you want to hear? ")
    response = call_model(user_input)
    print(response)


if __name__ == "__main__":
    main()