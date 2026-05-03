"""
Integration test for the voice-answer endpoint:
    POST /api/sessions/{session_id}/respond/audio

Strategy: the DB, S3, and AWS Transcribe are all mocked. This test verifies
only the new endpoint's behavior (validation, wiring, S3 cleanup on failure,
and the delegation to submit_response). The existing submit_response
function and models are not exercised.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def student_id():
    return uuid4()


@pytest.fixture
def other_student_id():
    return uuid4()


@pytest.fixture
def session_id():
    return uuid4()


@pytest.fixture
def fake_student(student_id):
    return SimpleNamespace(id=student_id, email="student@example.com")


@pytest.fixture
def fake_session(session_id, student_id):
    """An AssessmentSession owned by `student_id`, status 'in_progress'."""
    return SimpleNamespace(
        id=session_id,
        user_s_id=student_id,
        status="in_progress",
        started_at=None,
        assessment_config_id=None,
    )


@pytest.fixture
def mock_db(fake_session):
    """A MagicMock SQLAlchemy session whose .query().filter().first() returns
    the fake AssessmentSession."""
    db = MagicMock()
    chain = db.query.return_value.filter.return_value
    chain.first.return_value = fake_session
    return db


@pytest.fixture
def client(fake_student, mock_db, monkeypatch):
    """A TestClient with the dependencies and AWS calls overridden."""
    from app.main import app
    from app.core.database import get_db
    from app.core.dependencies import require_student

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[require_student] = lambda: fake_student

    # Stub S3
    monkeypatch.setattr(
        "app.api.routes.sessions.s3_client.upload_file",
        MagicMock(return_value="stub-key"),
    )
    monkeypatch.setattr(
        "app.api.routes.sessions.s3_client.delete_file",
        MagicMock(return_value=None),
    )

    # Stub the transcribe helper
    from app.utils.audio_transcriber import TranscribeResult

    monkeypatch.setattr(
        "app.api.routes.sessions.transcribe_audio_from_s3",
        MagicMock(
            return_value=TranscribeResult(
                text="my spoken answer to the question",
                job_name="job-abc",
                language_code="en-US",
            )
        ),
    )

    # Stub the downstream text-answer handler (we only want to assert we
    # delegate to it with the right payload; its behavior is tested elsewhere)
    async def fake_submit_response(*, session_id, payload, db, current_user):
        return {"next_question": None, "_received_text": payload.answer_text}

    monkeypatch.setattr(
        "app.api.routes.sessions.submit_response",
        AsyncMock(side_effect=fake_submit_response),
    )

    yield TestClient(app)

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_mp3(client, session_id):
    response = client.post(
        f"/api/sessions/{session_id}/respond/audio",
        files={"audio": ("answer.mp3", b"fake-audio-bytes", "audio/mpeg")},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("next_question") is None

    from app.api.routes import sessions as sessions_module

    # S3 upload called exactly once with an MP3 key under the session
    sessions_module.s3_client.upload_file.assert_called_once()
    (passed_bytes, passed_key), kwargs = sessions_module.s3_client.upload_file.call_args
    assert passed_bytes == b"fake-audio-bytes"
    assert passed_key.startswith(f"sessions/{session_id}/audio/")
    assert passed_key.endswith(".mp3")
    assert kwargs["content_type"] == "audio/mpeg"

    # Transcribe called with the same S3 key and extension 'mp3'
    sessions_module.transcribe_audio_from_s3.assert_called_once()
    t_args = sessions_module.transcribe_audio_from_s3.call_args.args
    assert t_args[0] == passed_key
    assert t_args[1] == "mp3"

    # Audio cleaned up from S3 after transcription
    sessions_module.s3_client.delete_file.assert_called_once_with(passed_key)

    # Downstream handler received the transcript as answer_text
    sessions_module.submit_response.assert_awaited_once()
    call_kwargs = sessions_module.submit_response.await_args.kwargs
    assert call_kwargs["session_id"] == session_id
    assert call_kwargs["payload"].answer_text == "my spoken answer to the question"


# ---------------------------------------------------------------------------
# Validation failures (should never reach S3/Transcribe)
# ---------------------------------------------------------------------------


def test_unsupported_extension_rejected(client, session_id):
    response = client.post(
        f"/api/sessions/{session_id}/respond/audio",
        files={"audio": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422
    assert "unsupported" in response.json()["detail"].lower()

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()
    sessions_module.transcribe_audio_from_s3.assert_not_called()


def test_empty_audio_rejected(client, session_id):
    response = client.post(
        f"/api/sessions/{session_id}/respond/audio",
        files={"audio": ("answer.wav", b"", "audio/wav")},
    )

    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()


# ---------------------------------------------------------------------------
# Session ownership / state
# ---------------------------------------------------------------------------


def test_session_not_found(client, session_id, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.post(
        f"/api/sessions/{session_id}/respond/audio",
        files={"audio": ("answer.wav", b"x", "audio/wav")},
    )

    assert response.status_code == 404

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()


def test_session_not_owned_by_caller(client, session_id, fake_session, other_student_id):
    # Session exists but belongs to a different student
    fake_session.user_s_id = other_student_id

    response = client.post(
        f"/api/sessions/{session_id}/respond/audio",
        files={"audio": ("answer.wav", b"x", "audio/wav")},
    )

    assert response.status_code == 403

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()


def test_session_already_completed(client, session_id, fake_session):
    fake_session.status = "completed"

    response = client.post(
        f"/api/sessions/{session_id}/respond/audio",
        files={"audio": ("answer.wav", b"x", "audio/wav")},
    )

    assert response.status_code == 409

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()


# ---------------------------------------------------------------------------
# Failure-cleanup invariants
# ---------------------------------------------------------------------------


def test_transcription_failure_deletes_uploaded_audio(client, session_id, monkeypatch):
    # Make transcription blow up
    monkeypatch.setattr(
        "app.api.routes.sessions.transcribe_audio_from_s3",
        MagicMock(side_effect=RuntimeError("boom")),
    )

    response = client.post(
        f"/api/sessions/{session_id}/respond/audio",
        files={"audio": ("answer.wav", b"bytes", "audio/wav")},
    )

    assert response.status_code == 502
    assert "transcription failed" in response.json()["detail"].lower()

    from app.api.routes import sessions as sessions_module

    # The audio was uploaded, then cleaned up even though the job failed
    sessions_module.s3_client.upload_file.assert_called_once()
    sessions_module.s3_client.delete_file.assert_called_once()

    # And we did NOT write an answer to the DB
    sessions_module.submit_response.assert_not_called()
