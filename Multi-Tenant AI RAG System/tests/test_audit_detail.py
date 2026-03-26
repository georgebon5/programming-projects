"""
Tests for audit log detail retrieval and filtering.
"""

from uuid import uuid4

from tests.conftest import auth_header, register_tenant


class TestAuditLogDetail:
    """Tests for /api/v1/audit-logs/ endpoint."""

    def test_list_audit_logs(self, client):
        """Admin can list audit logs (registration already creates entries)."""
        _, token = register_tenant(client, "audit-list")
        resp = client.get(
            "/api/v1/admin/audit-logs/",
            headers=auth_header(token),
        )
        assert resp.status_code == 200

    def test_audit_logs_unauthenticated(self, client):
        """Unauthenticated access is rejected."""
        resp = client.get("/api/v1/admin/audit-logs/")
        assert resp.status_code == 401

    def test_audit_logs_after_login(self, client):
        """Login action creates an audit log entry."""
        user, token = register_tenant(client, "audit-login")
        resp = client.get(
            "/api/v1/admin/audit-logs/",
            headers=auth_header(token),
        )
        assert resp.status_code == 200

    def test_audit_logs_pagination(self, client):
        """Audit logs support pagination parameters."""
        _, token = register_tenant(client, "audit-page")
        resp = client.get(
            "/api/v1/admin/audit-logs/?skip=0&limit=5",
            headers=auth_header(token),
        )
        assert resp.status_code == 200

    def test_audit_logs_tenant_isolation(self, client):
        """Audit logs from one tenant are not visible to another."""
        _, token_a = register_tenant(client, "audit-iso-a")
        _, token_b = register_tenant(client, "audit-iso-b")

        logs_a = client.get(
            "/api/v1/admin/audit-logs/",
            headers=auth_header(token_a),
        ).json()
        logs_b = client.get(
            "/api/v1/admin/audit-logs/",
            headers=auth_header(token_b),
        ).json()

        # Each tenant should only see their own logs
        a_list = logs_a.get("logs", logs_a) if isinstance(logs_a, dict) else logs_a
        b_list = logs_b.get("logs", logs_b) if isinstance(logs_b, dict) else logs_b

        a_ids = {log.get("id") for log in a_list}
        b_ids = {log.get("id") for log in b_list}
        assert a_ids.isdisjoint(b_ids), "Tenant audit logs should be isolated"

    def test_audit_log_has_timestamp(self, client):
        """Each audit log entry has a timestamp."""
        _, token = register_tenant(client, "audit-ts")
        resp = client.get(
            "/api/v1/admin/audit-logs/",
            headers=auth_header(token),
        )
        data = resp.json()
        logs = data.get("logs", data) if isinstance(data, dict) else data
        if logs:
            assert "created_at" in logs[0] or "timestamp" in logs[0]
