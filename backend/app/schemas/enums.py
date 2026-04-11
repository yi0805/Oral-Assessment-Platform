from enum import Enum

class UserRole(str, Enum):
    student = "student"
    instructor = "instructor"

class ProcessingStatus(str, Enum):
    uploaded = "uploaded"
    extracting = "extracting"
    chunking = "chunking"
    embedding = "embedding"
    ready = "ready"
    failed = "failed"


class PoolStatus(str, Enum):
    draft = "draft"
    reviewed = "reviewed"
    approved = "approved"
    archived = "archived"


class QuestionKind(str, Enum):
    main = "main"
    followup = "followup"
    probe = "probe"


class AnswerStyle(str, Enum):
    short = "short"
    long = "long"
    mixed = "mixed"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class AssessmentMode(str, Enum):
    generic = "generic"
    personalized = "personalized"


class AssessmentStatus(str, Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class SessionStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    submitted = "submitted"
    time_expired = "time_expired"
    under_review = "under_review"
    released = "released"


class GeneratedBy(str, Enum):
    approved_pool = "approved_pool"
    adaptive_ai = "adaptive_ai"
    instructor_override = "instructor_override"


class SenderRole(str, Enum):
    system = "system"
    assistant = "assistant"
    student = "student"
    instructor = "instructor"


class MessageType(str, Enum):
    main_question = "main_question"
    followup_question = "followup_question"
    student_answer = "student_answer"
    system_notice = "system_notice"
    summary_notice = "summary_notice"
