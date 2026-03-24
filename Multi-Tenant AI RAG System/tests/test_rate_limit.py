"""
Tests for rate limiting behavior.
"""

from app.main import app
from tests.conftest import register_tenant


class TestRateLimiting:
    def test_register_rate_limit(self, client):
        # Enable limiter explicitly for this test (disabled globally in conftest).
        app.state.limiter.enabled = True

        # 5 requests/min allowed, 6th should be blocked.
        for i in range(5):
            resp = client.post(
                "/api/v1/auth/register-tenant-admin",
                json={
                    "tenant_name": f"Rate Tenant {i}",
                    "tenant_slug": f"rate-{i}",
                    "username": "admin",
                    "email": f"admin{i}@rate.com",
                    "password": "password1234",
                },
            )
            assert resp.status_code == 201

        blocked = client.post(
            "/api/v1/auth/register-tenant-admin",
            json={
                "tenant_name": "Rate Tenant Blocked",
                "tenant_slug": "rate-blocked",
                "username": "admin",
                "email": "blocked@rate.com",
                "password": "password1234",
            },
        )
        assert blocked.status_code == 429

    def test_login_rate_limit(self, client):
        app.state.limiter.enabled = False
        register_tenant(client, "rate-login")
        app.state.limiter.enabled = True

        # 10/min allowed, 11th should be blocked.
        for _ in range(10):
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": "admin@rate-login.com", "password": "password1234"},
            )
            assert resp.status_code == 200

        blocked = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@rate-login.com", "password": "password1234"},
        )
        assert blocked.status_code == 429
