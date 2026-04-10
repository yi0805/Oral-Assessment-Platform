"""
Shared pytest fixtures for the Project 20 backend test suite.

Database strategy
-----------------
Tests run against a real PostgreSQL database whose URL is read from the
TEST_DATABASE_URL environment variable.  If that variable is not set the
entire test module is skipped automatically — no dummy SQLite is used because
pgvector's vector() column type is PostgreSQL-specific.

Isolation model
---------------
* session scope  – One engine + table setup for the whole test run.
* function scope – Every test gets its own DB transaction that is rolled back
                   after the test, so each test starts with a clean slate
                   without re-creating tables.

AI mocks
--------
The Gemini embedding client and the OpenRouter LLM client are both patched
with lightweight stubs so tests never call real external APIs and never need
API keys in CI.
"""
from __future__ import annotations

import os
import uuid
from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# ---------------------------------------------------------------------------
# Skip the whole suite if no test DB is configured
# ---------------------------------------------------------------------------

TEST_DB_URL: str | None = os.getenv("TEST_DATABASE_URL")

if not TEST_DB_URL:
    pytest.skip(
        "TEST_DATABASE_URL not set — skipping database-backed tests. "
        "Set it to a PostgreSQL URL, e.g. "
        "postgresql://project20:localdev123@localhost:5432/project20_test",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# Engine / session factory (session-scoped — created once per test run)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_engine():
    """Create an engine pointed at the test database."""
    engine = create_engine(TEST_DB_URL, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def setup_test_database(test_engine):
    """
    Create all ORM tables in the test database at the start of the session,
    and drop them at the end.

    Imports every model module so that SQLAlchemy's metadata is populated
    before create_all() is called.
    """
    # Import all models to register them with Base.metadata
    import app.models.user          # noqa: F401
    import app.models.course        # noqa: F401
    import app.models.material      # noqa: F401
    import app.models.rubric        # noqa: F401
    import app.models.question      # noqa: F401
    import app.models.assessment    # noqa: F401
    import app.models.session_runtime  # noqa: F401
    import app.models.feedback      # noqa: F401

    from app.core.database import Base

    # pgvector extension must exist before the vector column can be created
    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(test_engine, setup_test_database) -> Generator[Session, None, None]:
    """
    Yield a DB session wrapped in a transaction that is rolled back after each
    test.  This keeps tests isolated without re-creating tables.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient with DB override and AI mocks
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Return a TestClient that:
    * uses the rolled-back test DB session (via get_db override)
    * mocks out Gemini embedding and OpenRouter LLM calls
    """
    from app.core.database import get_db
    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with (
        patch("app.services.embedding_service.embed_text",
              new=AsyncMock(return_value=[0.0] * 768)),
        patch("app.services.embedding_service.embed_batch",
              new=AsyncMock(return_value=[[0.0] * 768])),
        patch("app.services.question_generator.generate_pool",
              new=AsyncMock(return_value=None)),
        patch("app.services.ai_summary_service.generate_summary",
              new=AsyncMock(return_value=None)),
        # Mock chat_complete so follow-up generation never hits OpenRouter in tests.
        # Returns a realistic-looking follow-up question so asked_text is always a
        # valid non-null string (asked_text is NOT NULL in session_question_items).
        patch("app.services.ai_gateway.chat_complete",
              new=AsyncMock(return_value="Can you elaborate further on that point?")),
    ):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_no_pipeline(db_session: Session) -> Generator[TestClient, None, None]:
    """
    TestClient that overrides get_db and mocks the background material
    processing pipeline (so uploads complete synchronously without
    spawning background tasks).
    """
    from app.core.database import get_db
    from app.main import app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    mock_pipeline = MagicMock()

    with (
        patch("app.services.material_pipeline.run_pipeline", mock_pipeline),
        patch("app.services.embedding_service.embed_text",
              new=AsyncMock(return_value=[0.0] * 768)),
    ):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Auth token helpers
# ---------------------------------------------------------------------------

def _make_token(client: TestClient, email: str, role: str) -> str:
    """Call the dev-token endpoint and return the access_token string."""
    resp = client.post(
        "/api/v1/auth/dev-token",
        json={"email": email, "role": role},
    )
    assert resp.status_code == 200, f"dev-token failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture
def instructor_token(client: TestClient) -> str:
    return _make_token(client, "instructor@test.com", "instructor")


@pytest.fixture
def student_token(client: TestClient) -> str:
    return _make_token(client, "student@test.com", "student")


@pytest.fixture
def instructor_headers(instructor_token: str) -> dict:
    return {"Authorization": f"Bearer {instructor_token}"}


@pytest.fixture
def student_headers(student_token: str) -> dict:
    return {"Authorization": f"Bearer {student_token}"}


# ---------------------------------------------------------------------------
# Reusable resource fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_course(client: TestClient, instructor_headers: dict) -> dict:
    """Create a course and return the response body."""
    resp = client.post(
        "/api/v1/courses",
        json={
            "course_code": "TEST101",
            "course_name": "Test Course",
            "term": "S1-2026",
            "description": "A course used in automated tests.",
        },
        headers=instructor_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def sample_rubric(client: TestClient, instructor_headers: dict, sample_course: dict) -> dict:
    """Create a rubric for sample_course and return the response body."""
    course_id = sample_course["id"]
    resp = client.post(
        f"/api/v1/courses/{course_id}/rubrics",
        json={
            "title": "Default Rubric",
            "content": "Grade on understanding: A=excellent, B=good, C=adequate, F=fail.",
        },
        headers=instructor_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def instructor_course_setup(client_no_pipeline: TestClient, db_session: Session) -> dict:
    """
    Create an instructor user + course and return a dict with:
      {
          "user":    <User ORM object>,
          "course":  <Course ORM object>,
          "token":   "<jwt>",
          "headers": {"Authorization": "Bearer <jwt>"},
      }
    This fixture targets client_no_pipeline so it can be shared with the
    S3 upload test.
    """
    from app.models.user import User
    from app.models.course import Course, CourseEnrollment
    from app.core.security import create_access_token

    # Create instructor user
    user = User(
        email=f"setup-instructor-{uuid.uuid4().hex[:8]}@test.com",
        full_name="Setup Instructor",
        role="instructor",
        status="active",
    )
    db_session.add(user)
    db_session.flush()

    # Create course
    course = Course(
        course_code="SETUP101",
        course_name="Setup Course",
        term="S1-2026",
        created_by=user.id,
    )
    db_session.add(course)
    db_session.flush()

    # Auto-enroll instructor
    enrollment = CourseEnrollment(
        course_id=course.id,
        user_id=user.id,
        course_role="instructor",
    )
    db_session.add(enrollment)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(course)

    token = create_access_token(
        user_id=str(user.id), role=user.role, email=user.email
    )
    return {
        "user": user,
        "course": course,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


# ---------------------------------------------------------------------------
# Full assessment setup — shared by test_sessions, test_feedback, test_questions
# ---------------------------------------------------------------------------

@pytest.fixture
def full_assessment_setup(client: TestClient, db_session: Session) -> dict:
    """
    Creates a complete, published assessment with:
      - An instructor user + student user
      - A course with both enrolled
      - A question pool with 2 approved main questions
      - A published AssessmentConfig linked to the pool

    Returns a dict with:
      {
        "instructor_headers": {...},
        "student_headers":    {...},
        "student_id":         "uuid-str",
        "instructor_id":      "uuid-str",
        "course_id":          "uuid-str",
        "pool_id":            "uuid-str",
        "assessment_id":      "uuid-str",
        "question_ids":       ["uuid", "uuid"],
      }

    Uses direct ORM inserts for speed (bypasses HTTP layer).
    """
    from datetime import datetime, timezone
    from app.models.user import User
    from app.models.course import Course, CourseEnrollment
    from app.models.question import Question, QuestionPool
    from app.models.assessment import AssessmentConfig
    from app.core.security import create_access_token

    uid = uuid.uuid4().hex[:8]

    # --- Users ---
    instructor = User(
        email=f"instr-{uid}@test.com", full_name="Test Instructor",
        role="instructor", status="active",
    )
    student = User(
        email=f"stud-{uid}@test.com", full_name="Test Student",
        role="student", status="active",
    )
    db_session.add_all([instructor, student])
    db_session.flush()

    # --- Course ---
    course = Course(
        course_code=f"TST{uid[:4].upper()}", course_name="Test Course",
        term="S1-2026", created_by=instructor.id,
    )
    db_session.add(course)
    db_session.flush()

    # --- Enrolments ---
    db_session.add_all([
        CourseEnrollment(course_id=course.id, user_id=instructor.id,
                         course_role="instructor", is_active=True),
        CourseEnrollment(course_id=course.id, user_id=student.id,
                         course_role="student", is_active=True),
    ])
    db_session.flush()

    # --- Question pool ---
    pool = QuestionPool(
        course_id=course.id, title="Auto Pool",
        generation_method="manual", created_by=instructor.id,
        status="approved",
        approved_by=instructor.id,
        approved_at=datetime.now(timezone.utc),
    )
    db_session.add(pool)
    db_session.flush()

    # --- 2 main questions ---
    q1 = Question(
        question_pool_id=pool.id,
        question_text="Explain the difference between a stack and a queue.",
        question_kind="main", answer_style="verbal",
        display_order=1, is_active=True, created_by=instructor.id,
    )
    q2 = Question(
        question_pool_id=pool.id,
        question_text="What is the time complexity of binary search?",
        question_kind="main", answer_style="verbal",
        display_order=2, is_active=True, created_by=instructor.id,
    )
    db_session.add_all([q1, q2])
    db_session.flush()

    # --- Assessment config (published) ---
    config = AssessmentConfig(
        course_id=course.id, question_pool_id=pool.id,
        title="Test Assessment", assessment_mode="generic",
        total_time_minutes=30, main_question_num=2,
        follow_up_num=1, followup_enabled=True,
        status="published",
        published_by=instructor.id,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(config)
    db_session.commit()

    instr_token = create_access_token(
        user_id=str(instructor.id), role=instructor.role, email=instructor.email
    )
    stud_token = create_access_token(
        user_id=str(student.id), role=student.role, email=student.email
    )

    return {
        "instructor_headers": {"Authorization": f"Bearer {instr_token}"},
        "student_headers":    {"Authorization": f"Bearer {stud_token}"},
        "instructor_id":      str(instructor.id),
        "student_id":         str(student.id),
        "course_id":          str(course.id),
        "pool_id":            str(pool.id),
        "assessment_id":      str(config.id),
        "question_ids":       [str(q1.id), str(q2.id)],
    }


# ---------------------------------------------------------------------------
# S3 mock (moto) — used only in test_materials_s3_upload.py
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_s3_bucket():
    """
    Spin up a moto-mocked S3 service, create the configured bucket, and
    patch the boto3 client used by the storage service so it points to moto.

    Yields the bucket name.
    """
    import boto3
    from moto import mock_aws

    from app.core.config import settings

    with mock_aws():
        s3 = boto3.client("s3", region_name=settings.aws_region)
        s3.create_bucket(
            Bucket=settings.s3_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": settings.aws_region},
        )
        # Override the storage backend for this test
        original_backend = settings.storage_backend
        settings.storage_backend = "s3"
        yield settings.s3_bucket_name
        settings.storage_backend = original_backend
