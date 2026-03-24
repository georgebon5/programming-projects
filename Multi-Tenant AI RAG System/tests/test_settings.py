"""
Tests for tenant settings and quota management.
"""

import io

from tests.conftest import auth_header, register_tenant


class TestTenantSettings:
    def test_get_default_settings(self, client):
        """New tenant gets default settings."""
        _, token = register_tenant(client, "settings-get")
        resp = client.get(
            "/api/v1/admin/settings/",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_users"] == 10
        assert data["max_documents"] == 100
        assert data["max_storage_mb"] == 500
        assert data["chat_enabled"] is True
        assert data["file_upload_enabled"] is True

    def test_update_settings(self, client):
        """Admin can update tenant settings."""
        _, token = register_tenant(client, "settings-upd")
        resp = client.patch(
            "/api/v1/admin/settings/",
            headers=auth_header(token),
            json={"max_users": 25, "max_documents": 500},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["max_users"] == 25
        assert data["max_documents"] == 500

    def test_partial_update(self, client):
        """Partial update should only change specified fields."""
        _, token = register_tenant(client, "settings-part")
        resp = client.patch(
            "/api/v1/admin/settings/",
            headers=auth_header(token),
            json={"chat_enabled": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["chat_enabled"] is False
        assert data["max_users"] == 10  # Unchanged


class TestUsage:
    def test_get_usage(self, client):
        """Get resource usage for tenant."""
        _, token = register_tenant(client, "usage")
        resp = client.get(
            "/api/v1/admin/settings/usage",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["users"]["current"] == 1  # The admin
        assert data["documents"]["current"] == 0
        assert "features" in data

    def test_usage_updates_after_upload(self, client):
        """Usage should reflect uploaded documents."""
        _, token = register_tenant(client, "usage-doc")
        content = "Doc for usage tracking. " * 50
        client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")},
        )
        resp = client.get(
            "/api/v1/admin/settings/usage",
            headers=auth_header(token),
        )
        data = resp.json()
        assert data["documents"]["current"] == 1
        assert data["storage_mb"]["current"] >= 0  # Small files can round to 0


class TestQuotaEnforcement:
    def test_user_quota_exceeded(self, client):
        """Cannot invite users beyond quota."""
        _, token = register_tenant(client, "quota-user")
        # Set max_users to 1 (admin already uses one)
        client.patch(
            "/api/v1/admin/settings/",
            headers=auth_header(token),
            json={"max_users": 1},
        )
        resp = client.post(
            "/api/v1/users/invite",
            headers=auth_header(token),
            json={
                "username": "extra",
                "email": "extra@quota-user.com",
                "password": "password1234",
            },
        )
        assert resp.status_code == 429

    def test_document_quota_exceeded(self, client):
        """Cannot upload documents beyond quota."""
        _, token = register_tenant(client, "quota-doc")
        # Set max_documents to 0
        client.patch(
            "/api/v1/admin/settings/",
            headers=auth_header(token),
            json={"max_documents": 0},
        )
        content = "Test content. " * 50
        resp = client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")},
        )
        assert resp.status_code == 429

    def test_chat_disabled(self, client):
        """Chat quota enforcement when disabled."""
        _, token = register_tenant(client, "quota-chat")
        # Disable chat
        client.patch(
            "/api/v1/admin/settings/",
            headers=auth_header(token),
            json={"chat_enabled": False},
        )
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "Should be blocked"},
        )
        assert resp.status_code == 429

    def test_upload_disabled(self, client):
        """Cannot upload when file_upload_enabled is False."""
        _, token = register_tenant(client, "quota-noup")
        client.patch(
            "/api/v1/admin/settings/",
            headers=auth_header(token),
            json={"file_upload_enabled": False},
        )
        content = "Blocked content. " * 50
        resp = client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")},
        )
        assert resp.status_code == 429
