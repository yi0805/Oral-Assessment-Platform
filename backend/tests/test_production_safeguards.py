"""Focused regressions for the production safeguards added in this release."""
from __future__ import annotations

import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile


def _query_result(*, first=None, all_rows=None):
    result = MagicMock()
    result.filter.return_value.first.return_value = first
    result.filter.return_value.all.return_value = [] if all_rows is None else all_rows
    return result


def test_cross_course_material_is_rejected_for_question_generation():
    """A UUID that does not resolve inside the requested course must not work."""
    from app.main import app
    from app.core.database import get_db
    from app.core.dependencies import require_instructor

    course_id = uuid4()
    foreign_material_id = uuid4()
    rubric_id = uuid4()
    instructor = SimpleNamespace(id=uuid4(), role="instructor")
    db = MagicMock()
    db.query.side_effect = [
        _query_result(first=SimpleNamespace(id=course_id)),  # course
        _query_result(first=SimpleNamespace()),  # instructor enrollment
        _query_result(first=SimpleNamespace(id=rubric_id)),  # rubric
        _query_result(all_rows=[]),  # material belongs to another course
    ]
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[require_instructor] = lambda: instructor

    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/courses/{course_id}/generate-question",
                json={
                    "material_ids": [str(foreign_material_id)],
                    "rubric_id": str(rubric_id),
                    "assessment_title": "Isolation test",
                    "total_time_minutes": 10,
                    "num_main_questions": 1,
                },
            )
        assert response.status_code == 409
        assert "another course" in response.json()["detail"]
        materials_query = db.query.call_args_list[3]
        assert materials_query.args, "The material lookup must be constrained in SQL."
    finally:
        app.dependency_overrides.clear()


def test_generation_fails_closed_when_rag_returns_no_context(monkeypatch):
    from app.services.question_generator import QuestionGenerationError, generate_pool

    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [
        SimpleNamespace(id=uuid4()),  # question pool
        SimpleNamespace(criteria_data=[]),  # rubric
    ]
    monkeypatch.setattr("app.services.question_generator.rag_search.search", AsyncMock(return_value=[]))
    llm = AsyncMock()
    monkeypatch.setattr("app.services.question_generator.smart_chat_complete", llm)

    try:
        asyncio.run(
            generate_pool(
                db=db,
                config_id=uuid4(),
                pool_id=uuid4(),
                material_ids=[uuid4()],
                rubric_id=uuid4(),
                num_main_questions=1,
            )
        )
        raise AssertionError("Expected QuestionGenerationError")
    except QuestionGenerationError as exc:
        assert "usable retrieved context" in str(exc)
    llm.assert_not_awaited()
    db.add.assert_not_called()


def test_material_pipeline_publishes_truthful_terminal_status(monkeypatch):
    from app.services import material_pipeline

    material_id = uuid4()
    statuses: list[str] = []
    monkeypatch.setattr(
        material_pipeline, "_set_material_status", lambda _id, state: statuses.append(state)
    )
    monkeypatch.setattr(material_pipeline, "_stage_extract", lambda _id: "source text")
    monkeypatch.setattr(material_pipeline, "_stage_chunk", lambda _id, _text: True)
    monkeypatch.setattr(material_pipeline, "_stage_embed", lambda _id: True)

    material_pipeline.run_pipeline(material_id)
    assert statuses == ["processing", "ready"]

    statuses.clear()
    monkeypatch.setattr(material_pipeline, "_stage_embed", lambda _id: False)
    material_pipeline.run_pipeline(material_id)
    assert statuses == ["processing", "failed"]


def test_non_pdf_upload_is_rejected_before_parsing():
    from app.utils.upload_validation import read_pdf_upload

    upload = UploadFile(filename="notes.txt", file=BytesIO(b"not a pdf"))
    try:
        asyncio.run(read_pdf_upload(upload))
        raise AssertionError("Expected invalid upload to be rejected")
    except Exception as exc:  # HTTPException is deliberately an API boundary type.
        assert getattr(exc, "status_code", None) == 422


def test_expensive_login_route_is_rate_limited():
    from app.main import app
    from app.core.database import get_db
    from app.core.limiter import limiter

    limiter.reset()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    try:
        with TestClient(app) as client:
            responses = [client.post("/api/auth/google/login") for _ in range(11)]
        assert all(response.status_code == 401 for response in responses[:10])
        assert responses[10].status_code == 429
    finally:
        limiter.reset()
        app.dependency_overrides.clear()


def test_health_endpoints_do_not_expose_database_details(monkeypatch):
    from app.main import app

    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "ok"}

        connect = MagicMock(side_effect=Exception("secret database host"))
        monkeypatch.setattr("app.main.engine.connect", connect)
        response = client.get("/health/ready")

    # An unexpected dependency exception should still be made safe at the API boundary.
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
