"""
Tests for GDPR data export and Request ID middleware.
"""

from tests.conftest import auth_header, register_tenant


class TestGDPRExport:
    def test_export_returns_user_data(self, client):
        user_data, token = register_tenant(client, "gdpr-exp")
        resp = client.get("/api/v1/me/export", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["email"] == user_data["email"]
        assert isinstance(data["documents"], list)
        assert isinstance(data["chat_messages"], list)
        assert isinstance(data["audit_logs"], list)
        # Registration + login should have produced audit logs
        assert len(data["audit_logs"]) >= 1

    def test_export_unauthenticated(self, client):
        resp = client.get("/api/v1/me/export")
        assert resp.status_code in (401, 403)


class TestRequestIDMiddleware:
    def test_response_has_request_id(self, client):
        resp = client.get("/health")
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) > 0

    def test_client_provided_request_id_honoured(self, client):
        resp = client.get("/health", headers={"X-Request-ID": "custom-123"})
        assert resp.headers["X-Request-ID"] == "custom-123"
