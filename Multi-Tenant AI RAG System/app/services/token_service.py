"""
TokenService – handles JWT blacklisting and token revocation checks.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.token_blacklist import BlacklistedToken


class TokenService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def blacklist_token(
        self,
        jti: str,
        token_type: str,
        user_id: UUID,
        tenant_id: UUID,
        expires_at: datetime,
    ) -> None:
        """Persist a token JTI as blacklisted so it cannot be reused."""
        entry = BlacklistedToken(
            jti=jti,
            token_type=token_type,
            user_id=user_id,
            tenant_id=tenant_id,
            expires_at=expires_at,
        )
        self.db.add(entry)
        self.db.commit()

    def is_blacklisted(self, jti: str) -> bool:
        """Return True if the given JTI has been explicitly revoked."""
        return (
            self.db.query(BlacklistedToken)
            .filter(BlacklistedToken.jti == jti)
            .first()
            is not None
        )

    def blacklist_all_user_tokens(self, user_id: UUID) -> int:
        """
        Revoke all outstanding tokens for a user by updating User.tokens_revoked_at.

        Because we cannot enumerate live JTIs, we rely on the timestamp approach:
        any token whose `iat` is before `tokens_revoked_at` will be rejected by
        `get_current_user`.  Returns 1 to indicate the revocation was recorded.
        """
        from datetime import timezone

        from app.models.user import User

        user = self.db.query(User).filter(User.id == user_id).first()
        if user is None:
            return 0
        user.tokens_revoked_at = datetime.now(timezone.utc)
        self.db.commit()
        return 1
