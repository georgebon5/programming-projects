"""
Tests for the expired token cleanup system.

Covers:
- CleanupService deletes expired records and leaves valid ones untouched.
- POST /api/v1/admin/cleanup requires ADMIN role.
- Non-admin users receive 403.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from tests.conftest import auth_header, register_tenant

# ── Timezone-aware helpers ─────────────────────────────────────────────────────

_UTC = timezone.utc


def _now() -> datetime:
    return datetime.now(_UTC)


def _past(**kwargs) -> datetime:
    return _now() - timedelta(**kwargs)


def _future(**kwargs) -> datetime:
    return _now() + timedelta(**kwargs)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ── CleanupService unit tests ──────────────────────────────────────────────────


class TestCleanupServicePasswordResetTokens:
    """CleanupService correctly handles PasswordResetToken records."""

    def _make_token(self, db, user_id, expires_at: datetime):
        from app.models.password_reset import PasswordResetToken

        tok = PasswordResetToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=_hash(str(uuid.uuid4())),
            expires_at=expires_at.replace(tzinfo=None),  # DB stores naive UTC
        )
        db.add(tok)
        db.commit()
        return tok

    def _get_user_id(self, db):
        from app.models.tenant import Tenant
        from app.models.user import User, UserRole

        tenant = Tenant(
            id=uuid.uuid4(),
            name="Cleanup Tenant",
            slug=f"cleanup-{uuid.uuid4().hex[:8]}",
        )
        db.add(tenant)
        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="cleanupuser",
            email=f"cleanup-{uuid.uuid4().hex[:6]}@test.com",
            hashed_password="x",
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        return user.id

    def test_expired_token_is_deleted(self, db):
        from app.services.cleanup_service import CleanupService

        user_id = self._get_user_id(db)
        self._make_token(db, user_id, expires_at=_past(hours=1))

        counts = CleanupService(db).cleanup_expired_tokens()
        assert counts["password_reset_tokens"] >= 1

    def test_valid_token_is_kept(self, db):
        from app.models.password_reset import PasswordResetToken
        from app.services.cleanup_service import CleanupService

        user_id = self._get_user_id(db)
        tok = self._make_token(db, user_id, expires_at=_future(hours=1))
        tok_id = tok.id
        db.expunge_all()

        CleanupService(db).cleanup_expired_tokens()

        remaining = db.query(PasswordResetToken).filter(PasswordResetToken.id == tok_id).first()
        assert remaining is not None

    def test_only_expired_tokens_deleted_mixed(self, db):
        from app.models.password_reset import PasswordResetToken
        from app.services.cleanup_service import CleanupService

        user_id = self._get_user_id(db)
        expired = self._make_token(db, user_id, expires_at=_past(minutes=5))
        valid = self._make_token(db, user_id, expires_at=_future(hours=2))
        # Capture IDs as plain values before the session state is mutated
        expired_id = expired.id
        valid_id = valid.id
        db.expunge_all()

        counts = CleanupService(db).cleanup_expired_tokens()
        assert counts["password_reset_tokens"] == 1

        assert db.query(PasswordResetToken).filter(PasswordResetToken.id == expired_id).first() is None
        assert db.query(PasswordResetToken).filter(PasswordResetToken.id == valid_id).first() is not None


class TestCleanupServiceEmailVerificationTokens:
    """CleanupService correctly handles EmailVerificationToken records."""

    def _make_token(self, db, user_id, expires_at: datetime):
        from app.models.email_verification import EmailVerificationToken

        tok = EmailVerificationToken(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=_hash(str(uuid.uuid4())),
            expires_at=expires_at.replace(tzinfo=None),
        )
        db.add(tok)
        db.commit()
        return tok

    def _get_user_id(self, db):
        from app.models.tenant import Tenant
        from app.models.user import User, UserRole

        tenant = Tenant(
            id=uuid.uuid4(),
            name="EmailVerify Tenant",
            slug=f"ev-{uuid.uuid4().hex[:8]}",
        )
        db.add(tenant)
        user = User(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            username="evuser",
            email=f"ev-{uuid.uuid4().hex[:6]}@test.com",
            hashed_password="x",
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        return user.id

    def test_expired_email_token_deleted(self, db):
        from app.services.cleanup_service import CleanupService

        user_id = self._get_user_id(db)
        self._make_token(db, user_id, expires_at=_past(hours=2))

        counts = CleanupService(db).cleanup_expired_tokens()
        assert counts["email_verification_tokens"] >= 1

    def test_valid_email_token_kept(self, db):
        from app.models.email_verification import EmailVerificationToken
        from app.services.cleanup_service import CleanupService

        user_id = self._get_user_id(db)
        tok = self._make_token(db, user_id, expires_at=_future(hours=24))
        tok_id = tok.id
        db.expunge_all()

        CleanupService(db).cleanup_expired_tokens()

        assert db.query(EmailVerificationToken).filter(EmailVerificationToken.id == tok_id).first() is not None


class TestCleanupServiceLoginAttempts:
    """CleanupService correctly handles LoginAttempt records."""

    def _make_attempt(self, db, locked_until: datetime, last_failed_at: datetime):
        from app.models.login_attempt import LoginAttempt

        attempt = LoginAttempt(
            id=uuid.uuid4(),
            email=f"test-{uuid.uuid4().hex[:6]}@test.com",
            failed_count=3,
            last_failed_at=last_failed_at.replace(tzinfo=None),
            locked_until=locked_until.replace(tzinfo=None),
        )
        db.add(attempt)
        db.commit()
        return attempt

    def test_old_unlocked_attempt_deleted(self, db):
        from app.services.cleanup_service import CleanupService

        # locked_until in the past, last_failed more than 24 h ago
        self._make_attempt(
            db,
            locked_until=_past(hours=2),
            last_failed_at=_past(hours=30),
        )

        counts = CleanupService(db).cleanup_expired_tokens()
        assert counts["old_login_attempts"] >= 1

    def test_still_locked_attempt_kept(self, db):
        from app.models.login_attempt import LoginAttempt
        from app.services.cleanup_service import CleanupService

        # locked_until still in the future
        attempt = self._make_attempt(
            db,
            locked_until=_future(hours=1),
            last_failed_at=_past(hours=30),
        )
        attempt_id = attempt.id
        db.expunge_all()

        CleanupService(db).cleanup_expired_tokens()

        assert db.query(LoginAttempt).filter(LoginAttempt.id == attempt_id).first() is not None

    def test_recent_failed_attempt_kept(self, db):
        from app.models.login_attempt import LoginAttempt
        from app.services.cleanup_service import CleanupService

        # locked_until past but last_failed only 1 h ago (< 24 h cutoff)
        attempt = self._make_attempt(
            db,
            locked_until=_past(hours=1),
            last_failed_at=_past(hours=1),
        )
        attempt_id = attempt.id
        db.expunge_all()

        CleanupService(db).cleanup_expired_tokens()

        assert db.query(LoginAttempt).filter(LoginAttempt.id == attempt_id).first() is not None


class TestCleanupServiceReturnsDict:
    """cleanup_expired_tokens always returns a dict with the expected keys."""

    def test_returns_expected_keys_on_empty_db(self, db):
        from app.services.cleanup_service import CleanupService

        counts = CleanupService(db).cleanup_expired_tokens()

        for key in (
            "password_reset_tokens",
            "email_verification_tokens",
            "expired_api_keys",
            "old_login_attempts",
        ):
            assert key in counts
            assert isinstance(counts[key], int)

    def test_all_zero_when_nothing_expired(self, db):
        from app.services.cleanup_service import CleanupService

        counts = CleanupService(db).cleanup_expired_tokens()
        assert all(v == 0 for v in counts.values())


# ── Admin endpoint tests ───────────────────────────────────────────────────────


class TestAdminCleanupEndpoint:
    """POST /api/v1/admin/cleanup requires ADMIN role."""

    def test_admin_can_trigger_cleanup(self, client, admin_token):
        resp = client.post(
            "/api/v1/admin/cleanup",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["detail"] == "Cleanup completed"
        assert "deleted" in data
        assert isinstance(data["deleted"], dict)

    def test_cleanup_response_contains_counts(self, client, admin_token):
        resp = client.post(
            "/api/v1/admin/cleanup",
            headers=auth_header(admin_token),
        )
        deleted = resp.json()["deleted"]
        for key in (
            "password_reset_tokens",
            "email_verification_tokens",
            "expired_api_keys",
            "old_login_attempts",
        ):
            assert key in deleted

    def test_member_cannot_trigger_cleanup(self, client, member_token):
        resp = client.post(
            "/api/v1/admin/cleanup",
            headers=auth_header(member_token),
        )
        assert resp.status_code == 403

    def test_unauthenticated_cannot_trigger_cleanup(self, client):
        resp = client.post("/api/v1/admin/cleanup")
        assert resp.status_code == 401

    def test_cleanup_deletes_expired_tokens_via_endpoint(self, client, admin_token, db):
        """End-to-end: insert an expired token, hit endpoint, confirm deletion."""
        from app.models.password_reset import PasswordResetToken
        from app.models.user import User

        # Fetch the admin user's id so we can attach the token
        admin_user = db.query(User).first()
        assert admin_user is not None

        expired_tok_id = uuid.uuid4()
        expired_tok = PasswordResetToken(
            id=expired_tok_id,
            user_id=admin_user.id,
            token_hash=_hash(str(uuid.uuid4())),
            expires_at=(_now() - timedelta(hours=1)).replace(tzinfo=None),
        )
        db.add(expired_tok)
        db.commit()
        # Detach so the session doesn't hold a stale reference after deletion
        db.expunge_all()

        resp = client.post(
            "/api/v1/admin/cleanup",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert resp.json()["deleted"]["password_reset_tokens"] >= 1

        # Token should be gone — query by raw id value, no cached object
        assert db.query(PasswordResetToken).filter(PasswordResetToken.id == expired_tok_id).first() is None
