"""
CleanupService — removes expired tokens and stale records from the database.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self, db: Session):
        self.db = db

    def cleanup_expired_tokens(self) -> dict[str, int]:
        """Remove all expired tokens and return counts per type."""
        now = datetime.now(UTC)
        counts: dict[str, int] = {}

        # 1. Expired password reset tokens
        from app.models.password_reset import PasswordResetToken

        result = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < now
        ).delete(synchronize_session=False)
        counts["password_reset_tokens"] = result

        # 2. Expired email verification tokens
        from app.models.email_verification import EmailVerificationToken

        result = self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.expires_at < now
        ).delete(synchronize_session=False)
        counts["email_verification_tokens"] = result

        # 3. Expired + inactive API keys
        from app.models.api_key import APIKey

        result = self.db.query(APIKey).filter(
            APIKey.expires_at.isnot(None),
            APIKey.expires_at < now,
            APIKey.is_active == False,  # noqa: E712
        ).delete(synchronize_session=False)
        counts["expired_api_keys"] = result

        # 4. Old login attempts (unlocked and older than 24 h)
        from app.models.login_attempt import LoginAttempt

        cutoff = now - timedelta(hours=24)
        result = self.db.query(LoginAttempt).filter(
            LoginAttempt.locked_until < now,
            LoginAttempt.last_failed_at < cutoff,
        ).delete(synchronize_session=False)
        counts["old_login_attempts"] = result

        # 5. Try to clean expired blacklisted tokens (if model exists)
        try:
            from app.models.token_blacklist import BlacklistedToken

            result = self.db.query(BlacklistedToken).filter(
                BlacklistedToken.expires_at < now
            ).delete(synchronize_session=False)
            counts["blacklisted_tokens"] = result
        except ImportError:
            pass

        self.db.commit()
        logger.info("Token cleanup completed: %s", counts)
        return counts
