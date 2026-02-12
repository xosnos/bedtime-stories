# Bedtime Stories (Take-Home Assignment)

This project generates bedtime stories for ages 5-10 using a storyteller + judge loop.
It keeps the required model (`gpt-3.5-turbo`) and improves output quality with bounded retries and rubric-based feedback.

## What This System Does

1. Takes a free-text story request from the user.
2. Normalizes it into a `StoryBrief` (bedtime goal, age band, target length).
3. Generates a story draft with strict safety and bedtime constraints.
4. Judges the draft on 5 rubric dimensions:
   - `safety`
   - `age_fit`
   - `coherence`
   - `engagement`
   - `language_simplicity`
5. Retries up to 3 total attempts using judge feedback if thresholds are not met.
6. Returns the best draft (with disclaimer if needed).
7. Supports one optional user revision, then re-runs judge evaluation.

## System Block Diagram

```mermaid
flowchart TD
    U[User] --> CLI[CLI App<br/>story_generator.py]
    CLI --> N[Request Normalizer<br/>normalize_user_request]
    N -->|Normalization prompt| M[(OpenAI gpt-3.5-turbo)]
    M --> N
    N --> B[StoryBrief]

    B --> O[Orchestrator<br/>generate_story_with_judge_loop]
    O --> S[Storyteller<br/>generate_story_draft]
    S -->|Story prompt (+ optional feedback)| M
    M --> S
    S --> D[StoryDraft]

    D --> J[Judge<br/>evaluate_story_draft]
    J -->|Judge rubric prompt| M
    M --> J
    J --> R[RubricScore]

    R --> T{Pass threshold?<br/>safety>=4<br/>coherence>=4<br/>avg>=4.0}
    T -->|Yes| F[Final Story]
    T -->|No + retries left| FB[Format failing feedback]
    FB --> O
    T -->|No + retries exhausted| BEST[Return best attempt + disclaimer]

    F --> REV{User wants revision?}
    BEST --> REV
    REV -->|Yes| HR[handle_user_revision]
    HR -->|Revision prompt| M
    M --> HR
    HR --> J
    REV -->|No| OUT[Display result]
    J --> OUT
```

## Prompt Flow Summary

- `normalize_user_request` prompt: extracts a concise bedtime goal.
- `generate_story_draft` prompt: enforces safety policy, age fit, calming tone, and target length.
- `evaluate_story_draft` prompt: scores the story (1-5) and returns parseable feedback.
- Retry loop: failing dimensions (<4) become feedback for the next storyteller prompt.
- Revision prompt: applies user change request while preserving safety constraints.

## Repository Structure

- `story_generator.py`: primary CLI entry point
- `main.py`: shared `call_model()` (OpenAI client wrapper)
- `storyteller.py`: request normalization + story draft generation
- `judge.py`: rubric evaluation + parser
- `orchestrator.py`: retry loop, threshold checks, revision flow
- `models.py`: dataclasses (`StoryBrief`, `StoryDraft`, `RubricScore`, `GenerationResult`)
- `tests/`: unit + property-style tests

## Setup and Run (venv + install + execute)

### 1. Create and activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `.env` in the project root:

```bash
OPENAI_API_KEY=your_api_key_here
```

### 4. Run the project

```bash
python story_generator.py
```

You can also run the simpler baseline CLI with:

```bash
python main.py
```

## Optional: Run Tests

```bash
pytest -q
```
