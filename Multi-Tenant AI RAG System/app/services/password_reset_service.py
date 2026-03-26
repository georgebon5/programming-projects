"""
Password reset service — handles forgot / reset password flow.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.password_reset import PasswordResetToken
from app.models.user import User
from app.services.email_service import send_email
from app.utils.security import hash_password, validate_password_strength


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class PasswordResetService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def request_reset(self, email: str) -> None:
        """Create a reset token and send the reset email.

        Always returns successfully to prevent email enumeration.
        """
        user = self.db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
        if user is None:
            return  # Silent — do not reveal whether the email exists

        # Invalidate any previous unused tokens for this user
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used.is_(False),
        ).update({"is_used": True})

        raw_token = secrets.token_urlsafe(48)
        expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
            minutes=settings.password_reset_expire_minutes
        )

        reset = PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=expires_at,
        )
        self.db.add(reset)
        self.db.commit()

        reset_link = f"{settings.frontend_url}/reset-password?token={raw_token}"
        send_email(
            to=email,
            subject="Password Reset Request",
            body=(
                f"Hello {user.username},\n\n"
                f"Click the link below to reset your password (valid for "
                f"{settings.password_reset_expire_minutes} minutes):\n\n"
                f"  {reset_link}\n\n"
                f"If you did not request this, you can safely ignore this email."
            ),
        )

    def reset_password(self, token: str, new_password: str) -> None:
        """Validate the token and set a new password."""
        validate_password_strength(new_password)

        token_hash = _hash_token(token)
        record = (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.is_used.is_(False),
            )
            .first()
        )
        if record is None:
            raise ValueError("Invalid or expired reset token")

        now = datetime.now(UTC)
        expires_at = record.expires_at.replace(
            tzinfo=UTC if record.expires_at.tzinfo is None else record.expires_at.tzinfo
        )
        if now > expires_at:
            record.is_used = True
            self.db.commit()
            raise ValueError("Reset token has expired")

        user = self.db.query(User).filter(User.id == record.user_id).first()
        if user is None or not user.is_active:
            raise ValueError("User not found or inactive")

        user.hashed_password = hash_password(new_password)
        record.is_used = True
        self.db.commit()
