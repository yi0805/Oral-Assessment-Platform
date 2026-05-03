"""Central schema registry. Import all Pydantic models for easy access."""

from app.schemas.enums import *

from app.schemas.user import UserResponse, GoogleLoginResponse, Userupi
from app.schemas.course import (
    CourseOut, CourseCreate, InstructorDashboardStudentRow, InstructorDashboardAssessmentOut, CourseInfoOut
)

from app.schemas.feedback import (
    ReleaseReview, ReleaseAllReviews, GradeUpdate, InstructorReviewUpdate, AISummaryInfoOut,
    ApproveAiReview, ApproveAllAiReviews, _SummaryLLMOutput
)

from app.schemas.assessment import (
    ReleaseResponse, AssessmentConfigInfoOut, AssessmentConfigDetailOut, AssessmentConfigUpdate,
    AssessmentConfigSummary, AssessmentHistoryItemOut, AssessmentHistoryOut, AssessmentTitleOut,
    SessionFeedbackOut, SessionInfoOut, PendingReviewOut, StudentInfoOut,
    TranscriptMessageOut, TranscriptDetailOut, StudentCourseAssessmentOut, StudentNextQuestionOut,
    StudentResponseRequest, StudentResponseResponse, SessionStartResponse, AssessmentCopyRequest
)

from app.schemas.question import (
   QuestionGenerationRequest, QuestionCreate, QuestionUpdate, QuestionOut, QuestionGenerationResponse
)

from app.schemas.rubric import (RubricCriteriaItem, RubricCreate, RubricOut)

from app.schemas.material import (GithubImportBody)