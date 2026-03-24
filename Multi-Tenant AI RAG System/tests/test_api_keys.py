"""
Tests for API key management and API key authentication.
"""


from tests.conftest import auth_header, register_tenant


class TestAPIKeysCRUD:
    def test_create_api_key(self, client):
        _, token = register_tenant(client, "ak-create")
        resp = client.post(
            "/api/v1/api-keys/",
            headers=auth_header(token),
            json={"name": "CI key"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "CI key"
        assert data["raw_key"].startswith("mtr_")
        assert data["is_active"] is True

    def test_list_api_keys(self, client):
        _, token = register_tenant(client, "ak-list")
        # Create two keys
        client.post("/api/v1/api-keys/", headers=auth_header(token), json={"name": "key1"})
        client.post("/api/v1/api-keys/", headers=auth_header(token), json={"name": "key2"})

        resp = client.get("/api/v1/api-keys/", headers=auth_header(token))
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_revoke_api_key(self, client):
        _, token = register_tenant(client, "ak-revoke")
        create_resp = client.post(
            "/api/v1/api-keys/",
            headers=auth_header(token),
            json={"name": "ephemeral"},
        )
        key_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_header(token))
        assert del_resp.status_code == 204

        # Key should still appear but be inactive
        keys = client.get("/api/v1/api-keys/", headers=auth_header(token)).json()
        assert any(k["id"] == key_id and k["is_active"] is False for k in keys)

    def test_revoke_nonexistent_key(self, client):
        _, token = register_tenant(client, "ak-404")
        resp = client.delete(
            "/api/v1/api-keys/00000000-0000-0000-0000-000000000000",
            headers=auth_header(token),
        )
        assert resp.status_code == 404


class TestAPIKeyAuth:
    def test_authenticate_with_api_key(self, client):
        """Full round-trip: create a key, then use it to call /auth/me."""
        _, token = register_tenant(client, "ak-auth")
        create_resp = client.post(
            "/api/v1/api-keys/",
            headers=auth_header(token),
            json={"name": "test-key"},
        )
        raw_key = create_resp.json()["raw_key"]

        # Use X-API-Key header instead of Bearer token
        me_resp = client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
        assert me_resp.status_code == 200
        assert me_resp.json()["email"].endswith("@ak-auth.com")

    def test_revoked_key_rejected(self, client):
        _, token = register_tenant(client, "ak-revoked")
        create_resp = client.post(
            "/api/v1/api-keys/",
            headers=auth_header(token),
            json={"name": "temp"},
        )
        raw_key = create_resp.json()["raw_key"]
        key_id = create_resp.json()["id"]

        # Revoke
        client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_header(token))

        # Should fail now
        resp = client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
        assert resp.status_code == 401

    def test_invalid_key_rejected(self, client):
        resp = client.get("/api/v1/auth/me", headers={"X-API-Key": "mtr_bogus"})
        assert resp.status_code == 401
