# Project 20 End-to-End User Flow

This backend is aligned to a single assessment workflow with two question-source modes:

- **Generic mode (MVP):** main questions come from an instructor-approved question pool generated from uploaded course materials.
- **Personalized mode (future phase):** main questions are generated from a student's uploaded submission, while the same chat runtime, timer, transcript storage, AI summary, and release workflow are reused.

## Instructor setup

1. Sign in with Google OAuth.
2. Create or select a course.
3. Upload reusable course materials.
4. Upload or define a rubric.
5. Create an assessment.

## Assessment configuration

An instructor can configure:

- title and instructions
- assessment mode (`generic` or `personalized`)
- rubric
- total session time limit
- optional per-question time limit
- maximum adaptive follow-ups per main question
- open and close timestamps
- publish status

### Main-question policy

The backend no longer stores a hard-coded `max_main_questions` value.

- In **generic mode**, the number of main questions is determined by the approved, active main questions in the selected question pool.
- In **personalized mode**, the number of main questions is determined by the instructor's runtime generation settings and the orchestration service.

This keeps the data model flexible and avoids baking presentation-time decisions into the database schema.

## Student assessment flow

1. Student signs in and opens an available assessment.
2. If the assessment is personalized, the student may upload the required submission first.
3. The session starts and the server records `started_at` and `expires_at`.
4. The system asks a main question.
5. The student answers.
6. The system may ask adaptive follow-up questions up to the configured limit.
7. The flow repeats until all main questions are exhausted or the total time expires.
8. The transcript is locked and stored for review.

## Instructor review and release

1. Instructor opens a completed session.
2. The backend shows the transcript and an AI-generated advisory summary.
3. The instructor enters the final grade and student-visible feedback.
4. The instructor releases the result.
5. After release, the student can view the final grade, feedback, and transcript.
