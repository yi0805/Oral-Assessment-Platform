"""
Integration tests for the input validation added to:
    POST /api/sessions/{session_id}/respond

Issue #71. The validation block at the top of submit_response trims
answer_text and rejects empty/whitespace-only/too-long values before
any DB work. These tests exercise that guard alone — the rest of
submit_response (session lookup, question advancement, transcript
write) has its own coverage and is out of scope here.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def session_id():
    return uuid4()


@pytest.fixture
def fake_student():
    return SimpleNamespace(id=uuid4(), email="student@example.com")


@pytest.fixture
def mock_db():
    """An empty MagicMock — the validation guard runs BEFORE any DB
    query, so the chain doesn't need to return anything meaningful for
    these tests. If the guard ever stops short-circuiting, the tests
    will start failing with AttributeError on the chain instead of
    silently passing."""
    return MagicMock()


@pytest.fixture
def client(fake_student, mock_db):
    from app.main import app
    from app.core.database import get_db
    from app.core.dependencies import require_student

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[require_student] = lambda: fake_student

    yield TestClient(app)

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Validation rejections (422)
# ---------------------------------------------------------------------------


def test_empty_answer_rejected(client, session_id, mock_db):
    response = client.post(
        f"/api/sessions/{session_id}/respond",
        json={"answer_text": ""},
    )

    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()

    # Guard short-circuits before any DB query
    mock_db.query.assert_not_called()


def test_whitespace_only_answer_rejected(client, session_id, mock_db):
    response = client.post(
        f"/api/sessions/{session_id}/respond",
        json={"answer_text": "   \n\t  "},
    )

    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()
    mock_db.query.assert_not_called()


def test_too_long_answer_rejected(client, session_id, mock_db):
    response = client.post(
        f"/api/sessions/{session_id}/respond",
        json={"answer_text": "x" * 10001},
    )

    assert response.status_code == 422
    assert "too long" in response.json()["detail"].lower()
    mock_db.query.assert_not_called()


# ---------------------------------------------------------------------------
# Boundary value: exactly 10000 characters should pass the validator and
# proceed to the next stage (where it'll error out due to our empty mock_db,
# but the important thing is that the validator did NOT reject it).
# ---------------------------------------------------------------------------


def test_max_length_answer_passes_validator(client, session_id, mock_db):
    # Make the DB return None for the session so the handler 404s — that
    # way we know we got past the validator without 422.
    mock_db.query.return_value.filter.return_value.first.return_value = None

    response = client.post(
        f"/api/sessions/{session_id}/respond",
        json={"answer_text": "x" * 10000},
    )

    # Validator allowed it through; session lookup then 404'd.
    assert response.status_code == 404
    assert response.status_code != 422
