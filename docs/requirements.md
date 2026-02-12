# Requirements Document

## Introduction

This document specifies requirements for a bedtime story generation system that uses an LLM judge to ensure age-appropriate, bedtime-safe content with consistent quality. The system builds upon an existing baseline (main.py) that accepts user prompts and returns unreviewed model responses. The enhanced system will implement a judge-driven quality improvement loop with bounded retries to ensure stories meet strict safety and quality standards for children aged 5-10.

## Glossary

- **Story_Generator**: The system component that accepts user requests and orchestrates the story generation workflow
- **Storyteller**: The LLM component that generates story drafts based on structured briefs
- **Judge**: The LLM component that evaluates story drafts against a structured rubric
- **Story_Brief**: A structured representation containing user_request, bedtime_goal, age_band, and target_length
- **Draft**: A generated story text produced by the Storyteller
- **Rubric_Score**: A structured evaluation containing safety, age_fit, coherence, engagement, and language_simplicity scores (1-5 scale)
- **Retry_Loop**: The bounded iteration process (maximum 3 attempts: 1 initial + 2 retries) for improving story quality
- **Pass_Threshold**: Minimum acceptable scores (safety >= 4, coherence >= 4, average >= 4.0)
- **User_Revision**: An optional user-directed modification request applied after the initial judge loop completes

## Requirements

### Requirement 1: Story Request Normalization

**User Story:** As a user, I want to provide a free-text story request, so that the system can generate an age-appropriate bedtime story tailored to my input.

#### Acceptance Criteria

1. WHEN a user provides a free-text story request, THE Story_Generator SHALL parse it into a Story_Brief containing user_request, bedtime_goal, age_band (5-10), and target_length (450-700 words)
2. THE Story_Generator SHALL preserve the original user_request text in the Story_Brief without modification
3. THE Story_Generator SHALL set age_band to 5-10 for all requests
4. THE Story_Generator SHALL set target_length to a value between 450 and 700 words
5. THE Story_Generator SHALL infer an appropriate bedtime_goal (e.g., "calming", "comforting", "gentle adventure") based on the user_request

### Requirement 2: Story Draft Generation

**User Story:** As a system, I want to generate story drafts with strict child-safety and bedtime-calming constraints, so that all content is appropriate for children aged 5-10 at bedtime.

#### Acceptance Criteria

1. WHEN the Storyteller receives a Story_Brief, THE Storyteller SHALL generate a Draft with a title and story text
2. THE Storyteller SHALL target a word count between 450 and 700 words
3. THE Storyteller SHALL use age-appropriate vocabulary and sentence complexity for ages 5-10
4. THE Storyteller SHALL create stories with a clear beginning, middle, and end
5. THE Storyteller SHALL maintain an emotionally warm and calming bedtime tone
6. THE Storyteller SHALL exclude graphic violence, intense horror, sexual/mature content, self-harm, drug/alcohol misuse, and sustained cruelty
7. WHEN generating a Draft, THE Storyteller SHALL use the gpt-3.5-turbo model

### Requirement 3: Story Quality Evaluation

**User Story:** As a system, I want to evaluate each story draft against a structured rubric, so that I can ensure consistent quality and safety standards.

#### Acceptance Criteria

1. WHEN the Judge receives a Draft, THE Judge SHALL evaluate it using a structured rubric with five dimensions: safety, age_fit, coherence, engagement, and language_simplicity
2. THE Judge SHALL assign a score from 1 to 5 for each rubric dimension
3. THE Judge SHALL provide specific feedback text for each dimension explaining the score
4. THE Judge SHALL return a Rubric_Score containing all dimension scores and feedback
5. WHEN evaluating safety, THE Judge SHALL assign a score of 4 or 5 only if the Draft contains no inappropriate content for ages 5-10
6. WHEN evaluating coherence, THE Judge SHALL assess whether the story has a clear narrative arc with beginning, middle, and end
7. WHEN evaluating age_fit, THE Judge SHALL assess vocabulary complexity and sentence structure appropriateness for ages 5-10
8. WHEN evaluating engagement, THE Judge SHALL assess whether the story maintains interest while remaining calming
9. WHEN evaluating language_simplicity, THE Judge SHALL assess whether word choice and sentence length are appropriate for the target age band
10. WHEN generating evaluations, THE Judge SHALL use the gpt-3.5-turbo model

### Requirement 4: Bounded Retry Loop

**User Story:** As a system, I want to iteratively improve story quality through bounded retries, so that I can deliver high-quality stories without infinite loops.

#### Acceptance Criteria

1. THE Story_Generator SHALL attempt story generation a maximum of 3 times (1 initial attempt + 2 retries)
2. WHEN a Draft receives a Rubric_Score, THE Story_Generator SHALL check if it meets Pass_Threshold (safety >= 4, coherence >= 4, average >= 4.0)
3. WHEN a Draft meets Pass_Threshold, THE Story_Generator SHALL accept the Draft and exit the Retry_Loop
4. WHEN a Draft fails Pass_Threshold and retry attempts remain, THE Story_Generator SHALL provide the Judge feedback to the Storyteller and request a new Draft
5. WHEN all retry attempts are exhausted, THE Story_Generator SHALL return the best available Draft (highest average score)
6. WHEN all retry attempts are exhausted and no Draft meets Pass_Threshold, THE Story_Generator SHALL include a disclaimer indicating quality standards were not fully met
7. THE Story_Generator SHALL track all Draft attempts and their corresponding Rubric_Score values

### Requirement 5: Quality Threshold Validation

**User Story:** As a system, I want to enforce minimum quality thresholds, so that only safe and coherent stories are accepted without disclaimer.

#### Acceptance Criteria

1. THE Story_Generator SHALL require safety score >= 4 for a Draft to pass
2. THE Story_Generator SHALL require coherence score >= 4 for a Draft to pass
3. THE Story_Generator SHALL require average score >= 4.0 across all five dimensions for a Draft to pass
4. WHEN calculating average score, THE Story_Generator SHALL compute the mean of safety, age_fit, coherence, engagement, and language_simplicity scores
5. WHEN a Draft meets all three threshold conditions, THE Story_Generator SHALL mark it as passing

### Requirement 6: User-Directed Revision

**User Story:** As a user, I want to request one optional revision to the generated story, so that I can refine the output to better match my preferences.

#### Acceptance Criteria

1. WHEN the Story_Generator completes the initial Retry_Loop, THE Story_Generator SHALL offer the user an option to request a revision
2. WHEN a user requests a revision, THE Story_Generator SHALL accept free-text revision instructions
3. WHEN processing a User_Revision, THE Story_Generator SHALL provide the revision instructions to the Storyteller along with the previous Draft
4. WHEN a revised Draft is generated, THE Story_Generator SHALL re-evaluate it using the Judge with the full rubric
5. WHEN a revised Draft is evaluated, THE Story_Generator SHALL apply the same Pass_Threshold criteria
6. THE Story_Generator SHALL support exactly one User_Revision per story generation session
7. WHEN a revised Draft fails Pass_Threshold, THE Story_Generator SHALL include a disclaimer indicating quality standards were not fully met

### Requirement 7: Judge Parse Failure Handling

**User Story:** As a system, I want to handle Judge response parsing failures gracefully, so that temporary LLM output issues don't break the workflow.

#### Acceptance Criteria

1. WHEN the Judge returns a response that cannot be parsed into a valid Rubric_Score, THE Story_Generator SHALL attempt to re-invoke the Judge once
2. WHEN the Judge retry also fails to parse, THE Story_Generator SHALL assign default failing scores (all dimensions = 3) and continue the workflow
3. WHEN using default failing scores, THE Story_Generator SHALL log a warning indicating Judge parse failure occurred
4. THE Story_Generator SHALL include parse failure information in the final output metadata

### Requirement 8: Safety Policy Enforcement

**User Story:** As a system, I want to enforce strict safety policies at multiple stages, so that inappropriate content is blocked for children aged 5-10.

#### Acceptance Criteria

1. THE Storyteller SHALL be instructed via system prompt to exclude graphic violence, intense horror, sexual/mature content, self-harm, drug/alcohol misuse, and sustained cruelty
2. THE Judge SHALL evaluate safety as a dedicated rubric dimension with explicit criteria for age 5-10 appropriateness
3. WHEN processing a User_Revision, THE Story_Generator SHALL re-apply all safety constraints through the Storyteller prompt
4. WHEN a User_Revision request contains inappropriate content suggestions, THE Storyteller SHALL decline to incorporate them and maintain safety standards
5. THE Story_Generator SHALL never return a Draft marked as passing if its safety score is below 4

### Requirement 9: Output and Metadata

**User Story:** As a user, I want to receive the final story along with quality metadata, so that I understand how the story was evaluated.

#### Acceptance Criteria

1. WHEN the Story_Generator completes, THE Story_Generator SHALL return the final Draft with its title and story text
2. THE Story_Generator SHALL include the final Rubric_Score with all dimension scores and feedback
3. THE Story_Generator SHALL include metadata showing the number of retry attempts used
4. WHEN a Draft does not meet Pass_Threshold, THE Story_Generator SHALL include a disclaimer message
5. THE Story_Generator SHALL include all historical Rubric_Score values from the Retry_Loop for transparency

### Requirement 10: Model Configuration

**User Story:** As a system, I want to use consistent model configuration, so that the implementation meets assignment constraints.

#### Acceptance Criteria

1. THE Story_Generator SHALL use gpt-3.5-turbo for all LLM calls (Storyteller and Judge)
2. THE Story_Generator SHALL not change the model from the baseline implementation
3. THE Story_Generator SHALL configure appropriate temperature settings for creative story generation and consistent evaluation
4. THE Story_Generator SHALL configure appropriate max_tokens limits to support target story length (450-700 words)
