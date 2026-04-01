"""
Tests for the unauthenticated health-check endpoints.

GET /              → root health check
GET /health/db     → database connectivity
GET /health/ai     → AI provider key configuration
GET /health/migrations → migration status
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Root health check
# ---------------------------------------------------------------------------

class TestRoot:
    def test_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_status_is_ok(self, client):
        body = client.get("/").json()
        assert body["status"] == "ok"

    def test_version_present(self, client):
        body = client.get("/").json()
        assert "version" in body
        assert body["version"]  # non-empty string


# ---------------------------------------------------------------------------
# Database health check
# ---------------------------------------------------------------------------

class TestHealthDb:
    def test_returns_200(self, client):
        response = client.get("/health/db")
        assert response.status_code == 200

    def test_database_connected(self, client):
        body = client.get("/health/db").json()
        assert body["status"] == "ok"
        assert body["database"] == "connected"

    def test_table_count_is_non_negative(self, client):
        body = client.get("/health/db").json()
        assert isinstance(body["public_tables"], int)
        assert body["public_tables"] >= 0


# ---------------------------------------------------------------------------
# AI provider configuration check
# ---------------------------------------------------------------------------

class TestHealthAi:
    def test_returns_200(self, client):
        response = client.get("/health/ai")
        assert response.status_code == 200

    def test_response_structure(self, client):
        body = client.get("/health/ai").json()
        assert body["status"] == "ok"
        assert "providers" in body
        providers = body["providers"]
        assert "embedding" in providers
        assert "chat" in providers

    def test_embedding_provider_fields(self, client):
        providers = client.get("/health/ai").json()["providers"]
        emb = providers["embedding"]
        assert emb["provider"] == "Google Gemini"
        assert "model" in emb
        assert "key_configured" in emb
        assert isinstance(emb["key_configured"], bool)

    def test_chat_provider_fields(self, client):
        providers = client.get("/health/ai").json()["providers"]
        chat = providers["chat"]
        assert chat["provider"] == "OpenRouter"
        assert "key_configured" in chat
        assert isinstance(chat["key_configured"], bool)


# ---------------------------------------------------------------------------
# Migration status check
# ---------------------------------------------------------------------------

class TestHealthMigrations:
    def test_returns_200(self, client):
        response = client.get("/health/migrations")
        assert response.status_code == 200

    def test_migrations_key_present(self, client):
        body = client.get("/health/migrations").json()
        assert "migrations" in body
        assert "status" in body

    def test_status_is_string(self, client):
        body = client.get("/health/migrations").json()
        assert body["status"] in ("ok", "incomplete", "error")
