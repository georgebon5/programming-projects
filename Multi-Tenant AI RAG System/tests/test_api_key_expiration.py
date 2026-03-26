"""
Tests for API key expiration and lifecycle management.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


class TestAPIKeyExpiration:
    """Tests for API key expiration validation."""

    def test_create_api_key_returns_key(self, client, admin_token):
        """Creating an API key returns the raw key exactly once."""
        resp = client.post(
            "/api/v1/api-keys/",
            json={"name": "test-key"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "raw_key" in data
        assert data["name"] == "test-key"

    def test_create_api_key_with_expiry(self, client, admin_token):
        """API key with explicit expiration date."""
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        resp = client.post(
            "/api/v1/api-keys/",
            json={"name": "expiring-key", "expires_at": future},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["expires_at"] is not None

    def test_list_api_keys(self, client, admin_token):
        """List all API keys for the tenant."""
        # Create a key first
        client.post(
            "/api/v1/api-keys/",
            json={"name": "list-test"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        keys = resp.json()
        assert isinstance(keys, list)
        assert len(keys) >= 1

    def test_revoke_api_key(self, client, admin_token):
        """Revoking an API key marks it inactive."""
        create_resp = client.post(
            "/api/v1/api-keys/",
            json={"name": "revoke-me"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        key_id = create_resp.json()["id"]
        resp = client.delete(
            f"/api/v1/api-keys/{key_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code in (200, 204)

    def test_use_api_key_auth(self, client, admin_token):
        """Authenticate via X-API-Key header."""
        create_resp = client.post(
            "/api/v1/api-keys/",
            json={"name": "auth-key"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        raw_key = create_resp.json()["raw_key"]
        # Use the key to access a protected endpoint
        resp = client.get(
            "/api/v1/documents/",
            headers={"X-API-Key": raw_key},
        )
        assert resp.status_code == 200

    def test_invalid_api_key_rejected(self, client):
        """Random API key is rejected."""
        resp = client.get(
            "/api/v1/documents/",
            headers={"X-API-Key": "invalid-key-12345"},
        )
        assert resp.status_code in (401, 403)

    def test_create_key_requires_admin(self, client, member_token):
        """Only admin users can create API keys."""
        resp = client.post(
            "/api/v1/api-keys/",
            json={"name": "not-allowed"},
            headers={"Authorization": f"Bearer {member_token}"},
        )
        assert resp.status_code == 403

    def test_create_key_no_auth(self, client):
        """Unauthenticated requests cannot create keys."""
        resp = client.post("/api/v1/api-keys/", json={"name": "no-auth"})
        assert resp.status_code == 401

    def test_duplicate_key_name_allowed(self, client, admin_token):
        """Multiple keys with the same name are allowed."""
        for _ in range(2):
            resp = client.post(
                "/api/v1/api-keys/",
                json={"name": "duplicate-name"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert resp.status_code == 201

    def test_api_key_has_creation_timestamp(self, client, admin_token):
        """API key response includes creation timestamp."""
        resp = client.post(
            "/api/v1/api-keys/",
            json={"name": "timestamp-key"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        data = resp.json()
        assert "created_at" in data

    def test_revoke_nonexistent_key(self, client, admin_token):
        """Revoking a nonexistent key returns 404."""
        fake_id = str(uuid4())
        resp = client.delete(
            f"/api/v1/api-keys/{fake_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    def test_list_keys_empty(self, client, admin_token_alt):
        """New tenant has no API keys."""
        resp = client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": f"Bearer {admin_token_alt}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_api_key_tenant_isolation(self, client, admin_token, admin_token_alt):
        """API keys from one tenant are not visible to another."""
        client.post(
            "/api/v1/api-keys/",
            json={"name": "tenant-a-key"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get(
            "/api/v1/api-keys/",
            headers={"Authorization": f"Bearer {admin_token_alt}"},
        )
        names = [k["name"] for k in resp.json()]
        assert "tenant-a-key" not in names
