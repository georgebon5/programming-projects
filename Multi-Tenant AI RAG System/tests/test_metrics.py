"""
Tests for custom Prometheus business-level metrics.

Verifies that:
- /metrics endpoint returns 200 and Prometheus text format
- Auth metrics are recorded after login and registration
- Chat metrics are recorded after a chat request
"""

import io
import uuid
from unittest.mock import patch

import pytest

from tests.conftest import auth_header, register_tenant


# ── Helpers ──────────────────────────────────────────────────────────────────

def _metrics_text(client) -> str:
    """Fetch /metrics and return the response body as a string."""
    resp = client.get("/metrics")
    assert resp.status_code == 200, f"/metrics returned {resp.status_code}"
    return resp.text


# ── /metrics endpoint ─────────────────────────────────────────────────────────

class TestMetricsEndpoint:
    def test_metrics_endpoint_returns_200(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        text = _metrics_text(client)
        # Prometheus text format always starts with '# HELP' or '# TYPE' lines
        assert "# HELP" in text or "# TYPE" in text

    def test_custom_metric_names_present(self, client):
        """After some activity the custom metric names should be visible."""
        # Trigger registration so counters get registered
        register_tenant(client)
        text = _metrics_text(client)

        expected_metrics = [
            "rag_auth_registrations_total",
            "rag_auth_login_attempts_total",
        ]
        for metric in expected_metrics:
            assert metric in text, f"Expected metric '{metric}' not found in /metrics output"


# ── Auth metrics ──────────────────────────────────────────────────────────────

class TestAuthMetrics:
    def test_registration_increments_metric(self, client):
        """A successful tenant registration should increment rag_auth_registrations_total."""
        slug = f"metrics-{uuid.uuid4().hex[:8]}"
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": f"Metrics Tenant {slug}",
                "tenant_slug": slug,
                "username": "admin",
                "email": f"admin@{slug}.com",
                "password": "Password1234!",
            },
        )
        assert resp.status_code == 201

        text = _metrics_text(client)
        assert "rag_auth_registrations_total" in text

    def test_successful_login_increments_metric(self, client):
        """A successful login should increment rag_auth_login_attempts_total{status='success'}."""
        slug = f"login-{uuid.uuid4().hex[:8]}"
        email = f"admin@{slug}.com"
        password = "Password1234!"

        # Register first
        client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": f"Login Tenant {slug}",
                "tenant_slug": slug,
                "username": "admin",
                "email": email,
                "password": password,
            },
        )

        # Now login
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert resp.status_code == 200

        text = _metrics_text(client)
        assert "rag_auth_login_attempts_total" in text
        assert 'status="success"' in text

    def test_failed_login_increments_metric(self, client):
        """A failed login should increment rag_auth_login_attempts_total{status='failed'}."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "WrongPassword1!"},
        )
        # 401 expected for bad credentials
        assert resp.status_code in (401, 400)

        text = _metrics_text(client)
        assert "rag_auth_login_attempts_total" in text
        assert 'status="failed"' in text


# ── Chat metrics ──────────────────────────────────────────────────────────────

class TestChatMetrics:
    def test_chat_request_increments_metric(self, client):
        """A chat request should record rag_chat_requests_total."""
        # Register tenant and mock vector store so no ChromaDB is needed
        _, token = register_tenant(client)

        with patch("app.services.chat_service.search_chunks", return_value=[]):
            resp = client.post(
                "/api/v1/chat/",
                headers=auth_header(token),
                json={"question": "What is AI?"},
            )

        assert resp.status_code == 200

        text = _metrics_text(client)
        assert "rag_chat_requests_total" in text

    def test_chat_response_duration_metric_present(self, client):
        """After a chat request, duration histogram metric should be present."""
        _, token = register_tenant(client)

        with patch("app.services.chat_service.search_chunks", return_value=[]):
            client.post(
                "/api/v1/chat/",
                headers=auth_header(token),
                json={"question": "Tell me about ML"},
            )

        text = _metrics_text(client)
        assert "rag_chat_response_duration_seconds" in text

    def test_chat_context_chunks_metric_present(self, client):
        """After a chat request, context chunks histogram metric should be present."""
        _, token = register_tenant(client)

        mock_chunks = [
            {"text": "AI is a field of CS", "document_id": str(uuid.uuid4()), "chunk_index": 0, "distance": 0.1}
        ]
        with patch("app.services.chat_service.search_chunks", return_value=mock_chunks):
            client.post(
                "/api/v1/chat/",
                headers=auth_header(token),
                json={"question": "What is AI?"},
            )

        text = _metrics_text(client)
        assert "rag_chat_context_chunks_used" in text

    def test_chat_mode_label_fallback(self, client):
        """Without a valid OpenAI key the mode label should be 'fallback'."""
        _, token = register_tenant(client)

        with patch("app.services.chat_service.search_chunks", return_value=[]), \
             patch("app.services.chat_service._has_valid_openai_key", return_value=False):
            client.post(
                "/api/v1/chat/",
                headers=auth_header(token),
                json={"question": "Hello"},
            )

        text = _metrics_text(client)
        assert "rag_chat_requests_total" in text
        assert 'mode="fallback"' in text
