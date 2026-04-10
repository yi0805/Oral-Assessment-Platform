"""Central model registry for SQLAlchemy relationship resolution."""

from app.models.assessment import AssessmentConfig, AssessmentSession
from app.models.course import Course, CourseEnrollment
from app.models.feedback import AISummary, SessionFeedback
from app.models.material import Material, MaterialChunk
from app.models.question import Question, QuestionPool
from app.models.session_runtime import SessionQuestionItem, TranscriptMessage
from app.models.user import User

__all__ = [
    "User",
    "Course",
    "CourseEnrollment",
    "Material",
    "MaterialChunk",
    "QuestionPool",
    "Question",
    "AssessmentConfig",
    "AssessmentSession",
    "SessionQuestionItem",
    "TranscriptMessage",
    "AISummary",
    "SessionFeedback",
]
