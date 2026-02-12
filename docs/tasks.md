# Implementation Plan: Bedtime Story Judge Loop

## Overview

This implementation plan breaks down the bedtime story generation system with LLM judge-driven quality improvement into incremental, testable steps. The plan follows a bottom-up approach: data models → core logic → orchestration → CLI integration → testing. Each task builds on previous work and includes specific requirement references for traceability.

The scope is designed for a short focused implementation, with property-based tests marked as optional for MVP delivery.

## Tasks

- [x] 1. Create data models and core data structures
  - Create models.py with StoryBrief, RubricScore, StoryDraft, and GenerationResult dataclasses
  - Implement average_score() and meets_threshold() methods on RubricScore
  - Ensure all dataclasses use proper type hints and Optional where needed
  - _Requirements: 1.1, 3.1, 3.2, 5.1, 5.2, 5.3, 5.4, 5.5, 9.1, 9.2, 9.3_

- [x] 1.1 Write unit tests for RubricScore methods
  - Test average_score() calculation with various score combinations
  - Test meets_threshold() with boundary cases (safety=3/4, coherence=3/4, average=3.9/4.0)
  - Test meets_threshold() returns True only when all three conditions met
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 1.2 Write property test for threshold logic
  - **Property 5: Threshold Logic Correctness**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.5**

- [x] 1.3 Write property test for average calculation
  - **Property 4: Average Score Calculation**
  - **Validates: Requirements 5.4**

- [x] 2. Implement Judge evaluation logic
  - [x] 2.1 Create judge.py with evaluate_story_draft() function
    - Build judge prompt with 5-dimension rubric (safety, age_fit, coherence, engagement, language_simplicity)
    - Use call_model() from main.py with temperature=0.1 for consistent evaluation
    - Return None if parsing fails (for retry handling)
    - _Requirements: 3.1, 3.2, 3.3, 3.10_
  
  - [x] 2.2 Implement parse_rubric_score() function
    - Parse judge response into RubricScore dataclass
    - Extract scores (1-5) and feedback text for all five dimensions
    - Raise exception if parsing fails
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [x] 2.3 Implement create_default_failing_score() function
    - Return RubricScore with all dimensions = 3
    - Set all feedback fields to "Judge evaluation failed to parse"
    - _Requirements: 7.2_

- [x] 2.4 Write unit tests for judge parsing
  - Test parse_rubric_score() with valid judge response format
  - Test parse_rubric_score() raises exception on missing fields
  - Test parse_rubric_score() raises exception on out-of-range scores
  - Test create_default_failing_score() returns all dimensions = 3
  - _Requirements: 3.1, 3.2, 3.3, 7.2_

- [x] 2.5 Write property test for rubric score structure
  - **Property 3: Rubric Score Structure Invariant**
  - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ] 3. Implement Storyteller generation logic
  - [x] 3.1 Create storyteller.py with normalize_user_request() function
    - Use call_model() to infer bedtime_goal from user input
    - Set age_band to (5, 10) and target_length to (450, 700)
    - Preserve original user_request unchanged
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [x] 3.2 Implement generate_story_draft() function
    - Build storyteller prompt with strict safety constraints
    - Include age_band, bedtime_goal, target_length from StoryBrief
    - Optionally include judge feedback for retry attempts
    - Use call_model() with temperature=0.8 for creative generation
    - Parse response to extract title and story_text
    - Calculate word_count
    - _Requirements: 2.1, 2.2, 2.6, 2.7, 8.1_

- [ ] 3.3 Write property test for story brief structure
  - **Property 1: Story Brief Structure Invariant**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

- [ ] 3.4 Write property test for story draft structure
  - **Property 2: Story Draft Structure Invariant**
  - **Validates: Requirements 2.1, 2.2**

- [x] 4. Checkpoint - Verify core components work independently
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement orchestration logic
  - [x] 5.1 Create orchestrator.py with generate_story_with_judge_loop() function
    - Implement bounded retry loop (max 3 attempts)
    - Generate draft, evaluate with judge, check threshold
    - Handle judge parse failures with single retry and default scores
    - Track best draft by average score
    - Exit early if threshold met
    - Return best draft with disclaimer if all attempts fail
    - Track all attempts and judge_parse_failures count
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 7.1, 7.2, 7.3, 7.4_
  
  - [x] 5.2 Implement format_judge_feedback() function
    - Format RubricScore into actionable feedback text
    - Include only dimensions with score < 4
    - Format as "DIMENSION (score X): feedback text"
    - _Requirements: 4.4_
  
  - [x] 5.3 Implement handle_user_revision() function
    - Build revision prompt with original story and user request
    - Include safety constraints in revision prompt
    - Generate revised draft using call_model()
    - Re-evaluate with judge (with parse failure handling)
    - Apply same threshold criteria
    - Return new GenerationResult with updated attempts list
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.7, 8.3_

- [x] 5.4 Write unit tests for feedback formatting
  - Test format_judge_feedback() with all scores >= 4 (empty feedback)
  - Test format_judge_feedback() with mixed scores (partial feedback)
  - Test format_judge_feedback() with all scores < 4 (full feedback)
  - _Requirements: 4.4_

- [x] 5.5 Write property test for bounded retry invariant
  - **Property 6: Bounded Retry Invariant**
  - **Validates: Requirements 4.1**

- [x] 5.6 Write property test for early exit behavior
  - **Property 7: Early Exit on Pass**
  - **Validates: Requirements 4.3**

- [x] 5.7 Write property test for best draft selection
  - **Property 8: Best Draft Selection**
  - **Validates: Requirements 4.5**

- [x] 5.8 Write property test for disclaimer on failure
  - **Property 9: Disclaimer on Failure**
  - **Validates: Requirements 4.6, 9.4**

- [x] 5.9 Write property test for generation result completeness
  - **Property 10: Generation Result Completeness**
  - **Validates: Requirements 4.7, 9.1, 9.2, 9.3, 9.5**

- [x] 5.10 Write property test for parse failure handling
  - **Property 11: Parse Failure Handling**
  - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 5.11 Write property test for safety invariant
  - **Property 12: Safety Invariant for Passing Stories**
  - **Validates: Requirements 8.5**

- [ ] 5.12 Write property test for revision re-evaluation
  - **Property 13: Revision Re-evaluation**
  - **Validates: Requirements 6.3, 6.4, 6.5, 6.7**

- [x] 6. Checkpoint - Verify orchestration logic works end-to-end
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create CLI interface
  - [x] 7.1 Create story_generator.py with main() function
    - Prompt user for story request
    - Call normalize_user_request() and display brief details
    - Call generate_story_with_judge_loop() with progress message
    - Display final story with title, text, word count, attempts, threshold status
    - Display disclaimer if present
    - Display all rubric scores and feedback
    - _Requirements: 1.1, 4.6, 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [x] 7.2 Add user revision workflow to main()
    - Prompt user for revision request (yes/no)
    - If yes, accept revision instructions
    - Call handle_user_revision() with progress message
    - Display revised story with same format as initial story
    - Display revised rubric scores
    - Support exactly one revision per session
    - _Requirements: 6.1, 6.2, 6.6_

- [ ] 8. Final integration and polish
  - [x] 8.1 Add if __name__ == "__main__" guard to story_generator.py
    - Ensure script can be run directly
    - _Requirements: 10.1_
  
  - [x] 8.2 Verify all imports work correctly
    - Test that models.py, storyteller.py, judge.py, orchestrator.py import correctly
    - Test that call_model() from main.py is accessible
    - _Requirements: 10.1, 10.2_
  
  - [ ] 8.3 Test with sample prompts
    - Run with "A story about a girl named Alice and her best friend Bob, who happens to be a cat."
    - Verify story generation, evaluation, and output display
    - Test revision workflow with a sample revision request
    - _Requirements: All_

- [ ] 9. Final checkpoint - Complete system verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks should be completed for a comprehensive implementation
- Core implementation (tasks 1-7) focuses on functionality, while tasks include comprehensive testing
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation and provide opportunities for user feedback
- The implementation preserves the existing main.py and call_model() function
- All LLM calls use gpt-3.5-turbo as required
- Property-based tests provide comprehensive coverage across all input variations
- Unit tests focus on specific examples and edge cases
