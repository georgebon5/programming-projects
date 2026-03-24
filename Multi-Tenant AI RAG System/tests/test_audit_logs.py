"""
Tests for admin audit logs API.
"""

import io

from tests.conftest import auth_header, register_tenant


class TestAuditLogs:
    def test_register_creates_audit_log(self, client):
        """Registration should create an audit log entry."""
        _, token = register_tenant(client, "audit-reg")
        resp = client.get(
            "/api/v1/admin/audit-logs/",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        actions = [log["action"] for log in data["logs"]]
        assert "register" in actions or "login" in actions

    def test_login_creates_audit_log(self, client):
        """Login should create an audit log entry."""
        _, token = register_tenant(client, "audit-login")
        resp = client.get(
            "/api/v1/admin/audit-logs/?action=login",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert all(log["action"] == "login" for log in data["logs"])

    def test_filter_by_action(self, client):
        """Filtering by action type should work."""
        _, token = register_tenant(client, "audit-filter")
        resp = client.get(
            "/api/v1/admin/audit-logs/?action=register",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(log["action"] == "register" for log in data["logs"])

    def test_upload_creates_audit_log(self, client):
        """Document upload should create an audit log entry."""
        _, token = register_tenant(client, "audit-upload")
        content = "Test content for audit. " * 50
        client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")},
        )
        resp = client.get(
            "/api/v1/admin/audit-logs/?action=document_upload",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    def test_non_admin_cannot_view_logs(self, client):
        """Non-admin users cannot access audit logs."""
        _, admin_token = register_tenant(client, "audit-perm")
        # Create a viewer
        client.post(
            "/api/v1/users/invite",
            headers=auth_header(admin_token),
            json={
                "username": "viewer",
                "email": "viewer@audit-perm.com",
                "password": "Password1234!",
                "role": "viewer",
            },
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@audit-perm.com", "password": "Password1234!"},
        )
        viewer_token = login.json()["access_token"]
        resp = client.get(
            "/api/v1/admin/audit-logs/",
            headers=auth_header(viewer_token),
        )
        assert resp.status_code == 403
