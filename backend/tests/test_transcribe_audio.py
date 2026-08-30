"""
Integration tests for the transcribe-only endpoint:
    POST /api/sessions/{session_id}/transcribe/audio

Issue #71. Strategy mirrors test_audio_answer.py — DB, S3, and AWS
Transcribe are mocked. The critical invariant exercised here that
distinguishes this endpoint from /respond/audio is:

    submit_response() must NEVER be called.

That guarantee is what lets the frontend show the transcript to the
student for editing before persisting via the standard text endpoint.
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
    db = MagicMock()
    chain = db.query.return_value.filter.return_value
    chain.first.return_value = fake_session
    return db


@pytest.fixture
def client(fake_student, mock_db, monkeypatch):
    from app.main import app
    from app.core.database import get_db
    from app.core.dependencies import require_student

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[require_student] = lambda: fake_student

    # The existing endpoint behaviour is tested with the feature enabled;
    # production defaults to disabled and has a separate regression test.
    monkeypatch.setattr("app.api.routes.sessions.settings.transcribe_enabled", True)

    monkeypatch.setattr(
        "app.api.routes.sessions.s3_client.upload_file",
        MagicMock(return_value="stub-key"),
    )
    monkeypatch.setattr(
        "app.api.routes.sessions.s3_client.delete_file",
        MagicMock(return_value=None),
    )

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

    # Spy on submit_response so we can assert it is NEVER called by the
    # transcribe endpoint. (If it ever gets called, the new flow has
    # regressed into the legacy auto-save path.)
    monkeypatch.setattr(
        "app.api.routes.sessions.submit_response",
        AsyncMock(return_value={"next_question": None}),
    )

    yield TestClient(app)

    app.dependency_overrides.clear()


def test_transcribe_returns_503_when_feature_is_disabled(
    fake_student, mock_db, session_id, monkeypatch
):
    from app.main import app
    from app.core.database import get_db
    from app.core.dependencies import require_student

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[require_student] = lambda: fake_student
    monkeypatch.setattr("app.api.routes.sessions.settings.transcribe_enabled", False)

    try:
        with TestClient(app) as disabled_client:
            response = disabled_client.post(
                f"/api/sessions/{session_id}/transcribe/audio",
                files={"audio": ("answer.webm", b"audio", "audio/webm")},
            )
        assert response.status_code == 503
        assert response.json()["detail"] == "Voice transcription is currently unavailable."
        mock_db.query.assert_not_called()
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_returns_transcript_only(client, session_id):
    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("answer.webm", b"fake-audio-bytes", "audio/webm")},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {"transcript": "my spoken answer to the question"}

    from app.api.routes import sessions as sessions_module

    # Audio uploaded under a session-scoped key with the correct extension
    sessions_module.s3_client.upload_file.assert_called_once()
    (passed_bytes, passed_key), kwargs = sessions_module.s3_client.upload_file.call_args
    assert passed_bytes == b"fake-audio-bytes"
    assert passed_key.startswith(f"sessions/{session_id}/audio/")
    assert passed_key.endswith(".webm")
    assert kwargs["content_type"] == "audio/webm"

    # Transcribe called with the same key
    sessions_module.transcribe_audio_from_s3.assert_called_once()
    t_args = sessions_module.transcribe_audio_from_s3.call_args.args
    assert t_args[0] == passed_key
    assert t_args[1] == "webm"

    # Audio cleaned up after success
    sessions_module.s3_client.delete_file.assert_called_once_with(passed_key)

    # CRITICAL: transcribe-only must not persist.
    sessions_module.submit_response.assert_not_called()


def test_happy_path_supports_mp3(client, session_id):
    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("answer.mp3", b"bytes", "audio/mpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {"transcript": "my spoken answer to the question"}


def test_empty_aws_transcript_returns_empty_string(client, session_id, monkeypatch):
    """If AWS returns empty text (silent audio), we still respond 200 with
    an empty transcript and let the frontend decide how to surface it."""
    from app.utils.audio_transcriber import TranscribeResult

    monkeypatch.setattr(
        "app.api.routes.sessions.transcribe_audio_from_s3",
        MagicMock(
            return_value=TranscribeResult(text="", job_name="j", language_code="en-US")
        ),
    )

    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("a.wav", b"x", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json() == {"transcript": ""}

    from app.api.routes import sessions as sessions_module
    sessions_module.submit_response.assert_not_called()


# ---------------------------------------------------------------------------
# Validation failures (must never reach S3/Transcribe/submit_response)
# ---------------------------------------------------------------------------


def test_unsupported_extension_rejected(client, session_id):
    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 422
    assert "unsupported" in response.json()["detail"].lower()

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()
    sessions_module.transcribe_audio_from_s3.assert_not_called()
    sessions_module.submit_response.assert_not_called()


def test_empty_audio_rejected(client, session_id):
    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("answer.wav", b"", "audio/wav")},
    )

    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()
    sessions_module.submit_response.assert_not_called()


# ---------------------------------------------------------------------------
# Session ownership / state
# ---------------------------------------------------------------------------


def test_session_not_found(client, session_id, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("a.wav", b"x", "audio/wav")},
    )

    assert response.status_code == 404

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()


def test_session_not_owned_by_caller(
    client, session_id, fake_session, other_student_id
):
    fake_session.user_s_id = other_student_id

    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("a.wav", b"x", "audio/wav")},
    )

    assert response.status_code == 403

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()


def test_session_already_completed(client, session_id, fake_session):
    fake_session.status = "completed"

    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("a.wav", b"x", "audio/wav")},
    )

    assert response.status_code == 409

    from app.api.routes import sessions as sessions_module
    sessions_module.s3_client.upload_file.assert_not_called()


# ---------------------------------------------------------------------------
# Failure-cleanup invariants
# ---------------------------------------------------------------------------


def test_transcription_failure_deletes_uploaded_audio_and_does_not_persist(
    client, session_id, monkeypatch
):
    monkeypatch.setattr(
        "app.api.routes.sessions.transcribe_audio_from_s3",
        MagicMock(side_effect=RuntimeError("boom")),
    )

    response = client.post(
        f"/api/sessions/{session_id}/transcribe/audio",
        files={"audio": ("a.wav", b"bytes", "audio/wav")},
    )

    assert response.status_code == 502
    assert "transcription failed" in response.json()["detail"].lower()

    from app.api.routes import sessions as sessions_module

    # Uploaded but cleaned up afterward
    sessions_module.s3_client.upload_file.assert_called_once()
    sessions_module.s3_client.delete_file.assert_called_once()

    # CRITICAL: failure path also must not persist anything.
    sessions_module.submit_response.assert_not_called()
