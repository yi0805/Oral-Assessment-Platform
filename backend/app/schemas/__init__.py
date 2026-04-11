"""Central schema registry. Import all Pydantic models for easy access."""

from app.schemas.enums import *
from app.schemas.user import UserResponse, GoogleLoginResponse
from app.schemas.course import (CourseOut, CourseCreate, InstructorDashboardStudentRow, InstructorDashboardAssessmentOut
)
from app.schemas.feedback import (
    ReleaseReview, ReleaseAllReviews, GradeUpdate, InstructorReviewUpdate
)
from app.schemas.assessment import (
    ReleaseResponse
)
from app.schemas.question import (
   UpdateNowRequest, 
)

from app.schemas.course import ( CourseUpdate, CourseOut, CourseBrief,
    EnrollmentCreate, EnrollmentOut, StudentListItem,
)
from app.schemas.material import (
    MaterialUploadResponse, MaterialOut, MaterialStatusOut, MaterialListItem,
    ChunkOut, RAGSearchRequest, RAGSearchResult, RAGSearchResponse,
)
from app.schemas.rubric import RubricCreate, RubricUpdate, RubricOut, RubricBrief
from app.schemas.question import (
    QuestionCreate, QuestionUpdate, QuestionOut,
    QuestionPoolCreate, QuestionPoolGenerateRequest, QuestionPoolOut, QuestionPoolBrief,
)
from app.schemas.assessment import (
    AssessmentConfigCreate, AssessmentConfigUpdate, AssessmentConfigOut, AssessmentConfigBrief,
    SessionStartResponse, StudentResponseRequest, StudentResponseResponse,
    SessionOut, SessionBrief, SessionBriefWithAIGrades, SessionQuestionItemOut, TranscriptMessageOut, FullTranscriptOut,
)
from app.schemas.feedback import (
    AISummaryOut, FeedbackCreate, FeedbackUpdate, FeedbackOut, StudentResultsOut,
)
