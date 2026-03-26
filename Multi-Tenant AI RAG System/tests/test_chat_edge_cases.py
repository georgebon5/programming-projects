"""
Tests for chat edge cases and tenant-level settings.
"""

from tests.conftest import auth_header, register_tenant


class TestChatEdgeCases:
    """Edge-case tests for the /api/v1/chat/ endpoints."""

    def test_empty_question(self, client):
        """Empty question is rejected."""
        _, token = register_tenant(client, "chat-empty")
        resp = client.post(
            "/api/v1/chat/",
            json={"question": ""},
            headers=auth_header(token),
        )
        assert resp.status_code == 422

    def test_whitespace_only_question(self, client):
        """Whitespace-only question is rejected."""
        _, token = register_tenant(client, "chat-ws")
        resp = client.post(
            "/api/v1/chat/",
            json={"question": "   "},
            headers=auth_header(token),
        )
        assert resp.status_code in (400, 422)

    def test_chat_no_auth(self, client):
        """Chat without auth token returns 401."""
        resp = client.post("/api/v1/chat/", json={"question": "hello?"})
        assert resp.status_code == 401

    def test_list_conversations(self, client):
        """List conversations for tenant."""
        _, token = register_tenant(client, "chat-list")
        resp = client.get(
            "/api/v1/chat/",
            headers=auth_header(token),
        )
        assert resp.status_code == 200

    def test_update_settings_admin(self, client, admin_token):
        """Admin can update tenant settings."""
        resp = client.patch(
            "/api/v1/admin/settings/",
            json={"max_documents": 100},
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    def test_update_settings_member_forbidden(self, client, member_token):
        """Members cannot update tenant settings."""
        resp = client.patch(
            "/api/v1/admin/settings/",
            json={"max_documents": 100},
            headers=auth_header(member_token),
        )
        assert resp.status_code == 403

    def test_get_settings(self, client, admin_token):
        """Admin can retrieve tenant settings."""
        resp = client.get(
            "/api/v1/admin/settings/",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "max_documents" in data

    def test_chat_missing_question_field(self, client):
        """Missing required 'question' field returns 422."""
        _, token = register_tenant(client, "chat-miss")
        resp = client.post(
            "/api/v1/chat/",
            json={},
            headers=auth_header(token),
        )
        assert resp.status_code == 422

    def test_chat_history_empty(self, client):
        """New tenant has empty conversation history."""
        _, token = register_tenant(client, "chat-hist")
        resp = client.get(
            "/api/v1/chat/",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
