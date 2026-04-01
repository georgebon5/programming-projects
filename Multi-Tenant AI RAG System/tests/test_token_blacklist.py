"""
Tests for JWT token blacklist, refresh token rotation, logout, and
password-change token revocation.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from tests.conftest import auth_header, register_tenant


class TestTokenBlacklistAfterLogout:
    def test_logout_invalidates_access_token(self, client):
        """After logout, the previously valid access token should be rejected."""
        _, token = register_tenant(client, f"lo-{uuid.uuid4().hex[:6]}")

        # Confirm the token works before logout
        resp = client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp.status_code == 200

        # Logout
        logout_resp = client.post(
            "/api/v1/auth/logout",
            json={},
            headers=auth_header(token),
        )
        assert logout_resp.status_code == 200
        assert logout_resp.json()["detail"] == "Logged out successfully"

        # The same token must now be rejected
        resp_after = client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp_after.status_code == 401

    def test_logout_invalidates_refresh_token(self, client):
        """After logout with refresh_token in body, that refresh token must be rejected."""
        slug = f"lo2-{uuid.uuid4().hex[:6]}"
        register_tenant(client, slug)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": f"admin@{slug}.com", "password": "Password1234!"},
        )
        assert login_resp.status_code == 200
        data = login_resp.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Logout with both tokens
        logout_resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers=auth_header(access_token),
        )
        assert logout_resp.status_code == 200

        # Using the blacklisted refresh token must now fail
        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401

    def test_logout_without_refresh_token(self, client):
        """Logout without a refresh_token body still succeeds."""
        _, token = register_tenant(client, f"lo3-{uuid.uuid4().hex[:6]}")
        resp = client.post(
            "/api/v1/auth/logout",
            json={},
            headers=auth_header(token),
        )
        assert resp.status_code == 200


class TestRefreshTokenRotation:
    def test_refresh_returns_new_token_pair(self, client):
        """Refresh endpoint returns a new access + refresh token."""
        slug = f"rt-{uuid.uuid4().hex[:6]}"
        register_tenant(client, slug)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": f"admin@{slug}.com", "password": "Password1234!"},
        )
        assert login_resp.status_code == 200
        data = login_resp.json()
        refresh_token = data["refresh_token"]

        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 200
        new_data = refresh_resp.json()
        assert "access_token" in new_data
        assert "refresh_token" in new_data
        # New tokens must differ from the originals
        assert new_data["access_token"] != data["access_token"]
        assert new_data["refresh_token"] != refresh_token

    def test_refresh_token_cannot_be_reused(self, client):
        """After rotation, the old refresh token must be blacklisted."""
        slug = f"rt2-{uuid.uuid4().hex[:6]}"
        register_tenant(client, slug)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": f"admin@{slug}.com", "password": "Password1234!"},
        )
        assert login_resp.status_code == 200
        old_refresh = login_resp.json()["refresh_token"]

        # First rotation — should succeed
        first_refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert first_refresh.status_code == 200

        # Reusing the consumed refresh token must fail
        second_refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert second_refresh.status_code == 401

    def test_new_access_token_after_rotation_is_valid(self, client):
        """The new access token obtained via refresh must authenticate correctly."""
        slug = f"rt3-{uuid.uuid4().hex[:6]}"
        register_tenant(client, slug)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": f"admin@{slug}.com", "password": "Password1234!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        new_access = refresh_resp.json()["access_token"]

        me_resp = client.get("/api/v1/auth/me", headers=auth_header(new_access))
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == f"admin@{slug}.com"


class TestPasswordChangeRevokesTokens:
    def test_old_token_rejected_after_password_change(self, client):
        """Changing password should set tokens_revoked_at, rejecting older tokens."""
        import time

        slug = f"pw-{uuid.uuid4().hex[:6]}"
        register_tenant(client, slug)
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": f"admin@{slug}.com", "password": "Password1234!"},
        )
        assert login_resp.status_code == 200
        old_token = login_resp.json()["access_token"]

        # Confirm old token works
        assert client.get("/api/v1/auth/me", headers=auth_header(old_token)).status_code == 200

        # Wait so the password-change revocation timestamp is strictly after the old token's iat
        time.sleep(1.1)

        # Change password
        pw_resp = client.put(
            "/api/v1/users/me/password",
            json={"current_password": "Password1234!", "new_password": "NewPassword5678!"},
            headers=auth_header(old_token),
        )
        assert pw_resp.status_code == 204

        # Old token should now be rejected
        me_resp = client.get("/api/v1/auth/me", headers=auth_header(old_token))
        assert me_resp.status_code == 401

    def test_new_login_works_after_password_change(self, client):
        """After password change the user can log in with the new password."""
        import time

        slug = f"pw2-{uuid.uuid4().hex[:6]}"
        register_tenant(client, slug)
        first_login = client.post(
            "/api/v1/auth/login",
            json={"email": f"admin@{slug}.com", "password": "Password1234!"},
        )
        old_token = first_login.json()["access_token"]

        # Wait so the revocation timestamp is strictly after the old token's iat
        time.sleep(1.1)

        client.put(
            "/api/v1/users/me/password",
            json={"current_password": "Password1234!", "new_password": "NewPassword5678!"},
            headers=auth_header(old_token),
        )

        # Wait so the new login token's iat is strictly after the revocation timestamp
        time.sleep(1.1)

        new_login = client.post(
            "/api/v1/auth/login",
            json={"email": f"admin@{slug}.com", "password": "NewPassword5678!"},
        )
        assert new_login.status_code == 200
        new_token = new_login.json()["access_token"]
        assert client.get("/api/v1/auth/me", headers=auth_header(new_token)).status_code == 200


class TestTokenServiceDirectly:
    def test_blacklist_and_check_jti(self, db):
        """Unit-test TokenService.blacklist_token and is_blacklisted directly."""
        from app.services.token_service import TokenService
        from app.models.tenant import Tenant
        from app.models.user import User, UserRole

        # Create a minimal tenant + user in the test DB
        tenant = Tenant(
            id=uuid.uuid4(),
            name=f"t-{uuid.uuid4().hex[:6]}",
            slug=f"sl-{uuid.uuid4().hex[:6]}",
        )
        db.add(tenant)
        db.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=f"u-{uuid.uuid4().hex[:6]}@test.com",
            username="u",
            hashed_password="x",
            role=UserRole.MEMBER,
        )
        db.add(user)
        db.commit()

        svc = TokenService(db)
        jti = str(uuid.uuid4())
        expires_at = datetime.now(UTC) + timedelta(minutes=15)

        assert svc.is_blacklisted(jti) is False

        svc.blacklist_token(
            jti=jti,
            token_type="access",
            user_id=user.id,
            tenant_id=tenant.id,
            expires_at=expires_at,
        )

        assert svc.is_blacklisted(jti) is True

    def test_blacklist_all_user_tokens_sets_revocation_timestamp(self, db):
        """blacklist_all_user_tokens should update User.tokens_revoked_at."""
        from app.services.token_service import TokenService
        from app.models.tenant import Tenant
        from app.models.user import User, UserRole

        tenant = Tenant(
            id=uuid.uuid4(),
            name=f"t2-{uuid.uuid4().hex[:6]}",
            slug=f"sl2-{uuid.uuid4().hex[:6]}",
        )
        db.add(tenant)
        db.flush()

        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            email=f"u2-{uuid.uuid4().hex[:6]}@test.com",
            username="u2",
            hashed_password="x",
            role=UserRole.MEMBER,
        )
        db.add(user)
        db.commit()

        assert user.tokens_revoked_at is None

        svc = TokenService(db)
        count = svc.blacklist_all_user_tokens(user.id)
        assert count == 1

        db.refresh(user)
        assert user.tokens_revoked_at is not None
