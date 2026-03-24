"""
Tests for authentication endpoints: register, login, /me.
"""

from tests.conftest import auth_header, register_tenant


class TestRegisterTenantAdmin:
    def test_register_success(self, client):
        user, token = register_tenant(client, "acme")
        assert user["email"] == "admin@acme.com"
        assert user["role"] == "admin"
        assert user["is_active"] is True

    def test_register_duplicate_slug(self, client):
        register_tenant(client, "dup")
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Dup2",
                "tenant_slug": "dup",
                "username": "u2",
                "email": "u2@dup.com",
                "password": "password1234",
            },
        )
        assert resp.status_code in (400, 422)

    def test_register_invalid_slug(self, client):
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Bad",
                "tenant_slug": "Bad Slug!",
                "username": "u",
                "email": "u@bad.com",
                "password": "password1234",
            },
        )
        assert resp.status_code == 422  # Pydantic validation

    def test_register_short_password(self, client):
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Pw",
                "tenant_slug": "pw",
                "username": "admin",
                "email": "a@pw.com",
                "password": "short",
            },
        )
        assert resp.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        register_tenant(client, "login-ok")
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@login-ok.com", "password": "password1234"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        register_tenant(client, "login-bad")
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@login-bad.com", "password": "wrongpassword1"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@nowhere.com", "password": "password1234"},
        )
        assert resp.status_code == 401


class TestMe:
    def test_me_success(self, client):
        user, token = register_tenant(client, "me-ok")
        resp = client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == user["email"]

    def test_me_no_token(self, client):
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 403  # HTTPBearer auto_error

    def test_me_invalid_token(self, client):
        resp = client.get(
            "/api/v1/auth/me",
            headers=auth_header("invalid.token.here"),
        )
        assert resp.status_code == 401
