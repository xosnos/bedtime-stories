# AGENTS.md

## Agent Persona

You are a Python engineer building the Bedtime Story project. Favor clear, explainable solutions over complex abstractions.

## Canonical Planning Sources

Use these documents together; do not treat any single file as complete by itself:

1. `docs/requirements.md` - normative acceptance criteria (WHAT must be true).
2. `docs/tasks.md` - implementation order and checkpoints (HOW we execute incrementally).
3. `docs/design.md` - architecture, data models, flow, properties, and test strategy.
4. `docs/prd.md` - product context, goals/non-goals, and requirement mapping.

If documents conflict:

- `docs/requirements.md` wins for behavior and acceptance criteria.
- `docs/tasks.md` wins for sequencing and scope checkpoints.
- `docs/design.md` guides architecture and interfaces unless it violates requirements.
- `docs/prd.md` provides intent and prioritization.

## Project Overview

This repository implements a bedtime story generation workflow with:

- user input normalization into a structured `StoryBrief`
- story generation via storyteller prompts
- judge-based rubric evaluation and bounded retries
- optional user-directed revision with safety re-check

Model constraint: keep using `gpt-3.5-turbo` for storyteller and judge flows.

## Build and Test Commands

- Install dependencies: `pip install -r requirements.txt`
- Run baseline script: `python main.py`
- Run enhanced generator (when implemented): `python story_generator.py`
- Run tests: `pytest -q`

## Coding Conventions

- Follow [PEP 8](https://peps.python.org) and readable, explicit Python.
- Use `snake_case` for variables/functions and `PascalCase` for classes.
- Keep modules focused (`models.py`, `storyteller.py`, `judge.py`, `orchestrator.py`).
- Add concise docstrings to public functions and data models.
- Prefer straightforward control flow over clever patterns.

## Workflow Rules

### Requirement-First Delivery

- Implement only behavior that traces to `docs/requirements.md` acceptance criteria.
- Preserve traceability by referencing requirement IDs in tests and task notes.
- Do not ship optional enhancements until baseline requirements pass.

### Task-Driven Execution

- Execute in small, testable increments following `docs/tasks.md`.
- Complete checkpoints before moving to later phases.
- Keep changes scoped to the current task unless a blocker forces adjacent edits.

### Design Alignment

- Match interfaces and invariants described in `docs/design.md`.
- Maintain bounded retry behavior and threshold logic exactly as defined.
- Keep safety constraints explicit in generation and revision prompts.

### Testing Expectations

- Add or update unit tests for each substantive behavior change.
- Preserve property-based test intent defined in `docs/design.md` and `docs/tasks.md`.
- Verify threshold and retry-loop behavior with deterministic tests/mocks where possible.

## Boundaries

- Never hard-code secrets, API keys, or credentials.
- Do not change model family from `gpt-3.5-turbo` unless requirements are updated.
- Avoid scope creep (web UI, frameworks, persistent memory) for MVP.
- Keep outputs safe for ages 5-10 and bedtime tone requirements.
