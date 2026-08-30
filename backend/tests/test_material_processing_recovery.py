"""Regression coverage for deploy-time material-processing safeguards."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from starlette.requests import Request


def _loopback_request(forwarded_for: str) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "headers": [(b"x-forwarded-for", forwarded_for.encode())],
            "client": ("127.0.0.1", 8000),
        }
    )


def test_documented_nginx_topology_overwrites_client_supplied_xff():
    config = (
        Path(__file__).resolve().parents[2] / "deployment" / "nginx.conf.example"
    ).read_text(encoding="utf-8")

    assert "$proxy_add_x_forwarded_for" not in config
    assert config.count("proxy_set_header X-Forwarded-For $remote_addr;") == 5


def test_limiter_uses_the_sanitized_nginx_client_identity():
    from app.core.limiter import get_trusted_client_ip

    # Nginx has already overwritten a browser-provided spoofed header with its
    # observed remote address before this loopback request reaches FastAPI.
    request = _loopback_request("203.0.113.10")
    assert get_trusted_client_ip(request) == "203.0.113.10"


def test_limiter_ignores_spoofed_forwarded_for_from_non_proxy_peer():
    from app.core.limiter import get_trusted_client_ip

    request = Request(
        {
            "type": "http",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "headers": [(b"x-forwarded-for", b"203.0.113.10")],
            "client": ("198.51.100.20", 8000),
        }
    )

    # Only loopback Nginx is trusted to supply the sanitized header.
    assert get_trusted_client_ip(request) == "198.51.100.20"


def test_migration_classifies_historical_materials_conservatively():
    migration = (
        Path(__file__).resolve().parents[1]
        / "sql"
        / "20260830_material_processing_and_question_provenance.sql"
    ).read_text(encoding="utf-8")

    assert "ADD COLUMN IF NOT EXISTS processing_status character varying;" in migration
    assert "WHERE chunk.material_id = material.id" in migration
    assert "chunk.embedding IS NULL OR vector_norm(chunk.embedding) = 0" in migration
    assert "THEN 'ready'" in migration
    assert "ELSE 'failed'" in migration
    assert "WHERE material.processing_status IS NULL;" in migration


def test_fresh_schema_defaults_new_materials_to_processing_with_timestamp_column():
    schema = (Path(__file__).resolve().parents[1] / "schema.sql").read_text(
        encoding="utf-8"
    )

    assert "processing_status character varying DEFAULT 'processing'::character varying NOT NULL" in schema
    assert "processing_started_at timestamp with time zone" in schema


def test_stale_processing_can_retry_but_active_processing_cannot():
    from app.core.config import settings
    from app.services.material_pipeline import can_retry_material_processing

    now = datetime.now(timezone.utc)
    stale = SimpleNamespace(
        processing_status="processing",
        processing_started_at=now
        - timedelta(seconds=settings.material_processing_stale_seconds + 1),
    )
    active = SimpleNamespace(
        processing_status="processing",
        processing_started_at=now
        - timedelta(seconds=settings.material_processing_stale_seconds - 1),
    )
    failed = SimpleNamespace(processing_status="failed", processing_started_at=None)

    assert can_retry_material_processing(stale, now=now)
    assert not can_retry_material_processing(active, now=now)
    assert can_retry_material_processing(failed, now=now)


def test_retry_endpoint_requeues_only_a_stale_processing_material(monkeypatch):
    from fastapi import BackgroundTasks, HTTPException
    from app.api.routes import materials
    from app.core.config import settings

    now = datetime.now(timezone.utc)
    material = SimpleNamespace(
        id=uuid4(),
        filename="interrupted.pdf",
        processing_status="processing",
        processing_started_at=now
        - timedelta(seconds=settings.material_processing_stale_seconds + 1),
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.with_for_update.return_value.first.return_value = material
    monkeypatch.setattr(materials, "_require_course_instructor", lambda *_args: None)

    result = materials.retry_material_processing(
        course_id=uuid4(),
        material_id=material.id,
        background_tasks=BackgroundTasks(),
        db=db,
        current_user=SimpleNamespace(),
    )

    assert result.processing_status == "processing"
    assert not result.is_processing_stale
    assert material.processing_started_at > now
    db.commit.assert_called_once()

    material.processing_started_at = now
    with pytest.raises(HTTPException, match="Only failed or interrupted") as exc_info:
        materials.retry_material_processing(
            course_id=uuid4(),
            material_id=material.id,
            background_tasks=BackgroundTasks(),
            db=db,
            current_user=SimpleNamespace(),
        )
    assert exc_info.value.status_code == 409


def test_terminal_status_clears_processing_timestamp(monkeypatch):
    from app.services import material_pipeline

    material = SimpleNamespace(
        processing_status="processing",
        processing_started_at=datetime.now(timezone.utc),
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = material
    monkeypatch.setattr(material_pipeline, "_get_db", lambda: db)

    material_pipeline._set_material_status(uuid4(), "ready")

    assert material.processing_status == "ready"
    assert material.processing_started_at is None
    db.commit.assert_called_once()
