"""
Email verification service — handles sending verification emails and confirming tokens.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.services.email_service import send_email

_VERIFICATION_EXPIRE_HOURS = 48


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class EmailVerificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def send_verification(self, user: User) -> None:
        """Create a verification token and email it to the user."""
        # Invalidate previous unused tokens
        self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.is_used.is_(False),
        ).update({"is_used": True})

        raw_token = secrets.token_urlsafe(48)
        expires_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(
            hours=_VERIFICATION_EXPIRE_HOURS
        )

        record = EmailVerificationToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=expires_at,
        )
        self.db.add(record)
        self.db.commit()

        verify_link = f"{settings.frontend_url}/verify-email?token={raw_token}"
        send_email(
            to=user.email,
            subject="Verify your email address",
            body=(
                f"Hello {user.username},\n\n"
                f"Please verify your email address by clicking the link below "
                f"(valid for {_VERIFICATION_EXPIRE_HOURS} hours):\n\n"
                f"  {verify_link}\n\n"
                f"If you did not create an account, you can ignore this email."
            ),
        )

    def verify(self, token: str) -> User:
        """Validate the token and mark the user as email-verified."""
        token_hash = _hash_token(token)
        record = (
            self.db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.token_hash == token_hash,
                EmailVerificationToken.is_used.is_(False),
            )
            .first()
        )
        if record is None:
            raise ValueError("Invalid or expired verification token")

        now = datetime.now(UTC)
        expires_at = record.expires_at.replace(
            tzinfo=UTC if record.expires_at.tzinfo is None else record.expires_at.tzinfo
        )
        if now > expires_at:
            record.is_used = True
            self.db.commit()
            raise ValueError("Verification token has expired")

        user = self.db.query(User).filter(User.id == record.user_id).first()
        if user is None:
            raise ValueError("User not found")

        user.is_email_verified = True
        record.is_used = True
        self.db.commit()
        self.db.refresh(user)
        return user
