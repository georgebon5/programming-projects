"""
Tests for new security features:
- Password complexity validation
- Account lockout after failed logins
- JWT refresh tokens
"""

from unittest.mock import patch

from tests.conftest import auth_header, register_tenant


class TestPasswordComplexity:
    """Password must have uppercase, lowercase, digit, and special char."""

    def test_register_weak_no_uppercase(self, client):
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Weak",
                "tenant_slug": "weak-upper",
                "username": "admin",
                "email": "a@weak-upper.com",
                "password": "password1234!",
            },
        )
        assert resp.status_code == 400
        assert "uppercase" in resp.json()["detail"].lower()

    def test_register_weak_no_lowercase(self, client):
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Weak",
                "tenant_slug": "weak-lower",
                "username": "admin",
                "email": "a@weak-lower.com",
                "password": "PASSWORD1234!",
            },
        )
        assert resp.status_code == 400
        assert "lowercase" in resp.json()["detail"].lower()

    def test_register_weak_no_digit(self, client):
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Weak",
                "tenant_slug": "weak-digit",
                "username": "admin",
                "email": "a@weak-digit.com",
                "password": "Passwordnodigit!",
            },
        )
        assert resp.status_code == 400
        assert "digit" in resp.json()["detail"].lower()

    def test_register_weak_no_special(self, client):
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Weak",
                "tenant_slug": "weak-special",
                "username": "admin",
                "email": "a@weak-special.com",
                "password": "Password1234",
            },
        )
        assert resp.status_code == 400
        assert "special" in resp.json()["detail"].lower()

    def test_register_strong_password_ok(self, client):
        resp = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Strong",
                "tenant_slug": "strong-pw",
                "username": "admin",
                "email": "a@strong-pw.com",
                "password": "StrongPass1!",
            },
        )
        assert resp.status_code == 201


class TestAccountLockout:
    """Account gets locked after max_login_attempts failed logins."""

    def test_lockout_after_max_attempts(self, client):
        # Register a real user
        register_tenant(client, "lockout-test")

        # Fail login 5 times (default max_login_attempts=5)
        for _ in range(5):
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": "admin@lockout-test.com", "password": "WrongPass9!"},
            )
            assert resp.status_code in (401, 429)

        # 6th attempt should be locked (429)
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@lockout-test.com", "password": "Password1234!"},
        )
        assert resp.status_code == 429
        assert "locked" in resp.json()["detail"].lower()

    def test_lockout_clears_on_success(self, client):
        register_tenant(client, "lockout-clear")

        # Fail a few times (under the limit)
        for _ in range(3):
            client.post(
                "/api/v1/auth/login",
                json={"email": "admin@lockout-clear.com", "password": "WrongPass9!"},
            )

        # Successful login clears counter
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@lockout-clear.com", "password": "Password1234!"},
        )
        assert resp.status_code == 200

        # Fail a few more — should NOT trigger lockout (counter was reset)
        for _ in range(3):
            client.post(
                "/api/v1/auth/login",
                json={"email": "admin@lockout-clear.com", "password": "WrongPass9!"},
            )

        # Still under the limit, should get 401 not 429
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@lockout-clear.com", "password": "WrongPass9!"},
        )
        assert resp.status_code == 401

    def test_lockout_unknown_email_no_crash(self, client):
        """Lockout tracker should work even for non-existent emails."""
        for _ in range(6):
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": "ghost@nowhere.com", "password": "WrongPass9!"},
            )
        assert resp.status_code == 429


class TestRefreshToken:
    """JWT refresh token flow."""

    def test_login_returns_refresh_token(self, client):
        register_tenant(client, "refresh-basic")
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@refresh-basic.com", "password": "Password1234!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "refresh_token" in data
        assert data["refresh_token"] is not None

    def test_refresh_returns_new_tokens(self, client):
        register_tenant(client, "refresh-flow")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@refresh-flow.com", "password": "Password1234!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in_seconds"] > 0

    def test_refresh_with_access_token_fails(self, client):
        """Using an access token as refresh should fail."""
        register_tenant(client, "refresh-bad")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@refresh-bad.com", "password": "Password1234!"},
        )
        access_token = login_resp.json()["access_token"]

        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
        assert resp.status_code == 401

    def test_refresh_with_invalid_token(self, client):
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert resp.status_code == 401

    def test_refreshed_token_works_for_me(self, client):
        """Access token from refresh should authenticate /me."""
        register_tenant(client, "refresh-me")
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@refresh-me.com", "password": "Password1234!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        new_access = refresh_resp.json()["access_token"]

        me_resp = client.get("/api/v1/auth/me", headers=auth_header(new_access))
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "admin@refresh-me.com"
