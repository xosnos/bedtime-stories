from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StoryBrief:
    """Structured representation of user story request."""
    user_request: str
    bedtime_goal: str
    age_band: tuple[int, int]  # Always (5, 10)
    target_length: tuple[int, int]  # Always (450, 700)


@dataclass
class RubricScore:
    """Evaluation scores and feedback for a story draft."""
    safety: int  # 1-5
    age_fit: int  # 1-5
    coherence: int  # 1-5
    engagement: int  # 1-5
    language_simplicity: int  # 1-5
    safety_feedback: str
    age_fit_feedback: str
    coherence_feedback: str
    engagement_feedback: str
    language_simplicity_feedback: str

    def average_score(self) -> float:
        """Calculate average across all dimensions."""
        return (self.safety + self.age_fit + self.coherence +
                self.engagement + self.language_simplicity) / 5.0

    def meets_threshold(self) -> bool:
        """Check if scores meet pass threshold."""
        return (self.safety >= 4 and
                self.coherence >= 4 and
                self.average_score() >= 4.0)


@dataclass
class StoryDraft:
    """A generated story with metadata."""
    title: str
    story_text: str
    word_count: int
    rubric_score: Optional[RubricScore] = None


@dataclass
class GenerationResult:
    """Final output with story and metadata."""
    final_draft: StoryDraft
    all_attempts: List[tuple[StoryDraft, RubricScore]]
    retry_count: int
    passed_threshold: bool
    disclaimer: Optional[str] = None
    judge_parse_failures: int = 0
    revision_used: bool = False
