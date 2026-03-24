"""
Service layer for API key CRUD and validation.
"""

import hashlib
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.api_key import APIKey, _generate_api_key


def _hash_key(raw_key: str) -> str:
    """One-way SHA-256 hash of the API key (never store plaintext)."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


class APIKeyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_key(
        self,
        tenant_id: UUID,
        user_id: UUID,
        name: str,
        expires_at: datetime | None = None,
    ) -> tuple[APIKey, str]:
        """Create a new API key. Returns (db_object, raw_key)."""
        raw_key = _generate_api_key()
        key_obj = APIKey(
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            key_hash=_hash_key(raw_key),
            key_prefix=raw_key[:12],
            expires_at=expires_at,
        )
        self.db.add(key_obj)
        self.db.commit()
        self.db.refresh(key_obj)
        return key_obj, raw_key

    def list_keys(self, user_id: UUID) -> list[APIKey]:
        return (
            self.db.query(APIKey)
            .filter(APIKey.user_id == user_id)
            .order_by(APIKey.created_at.desc())
            .all()
        )

    def revoke_key(self, key_id: UUID, user_id: UUID) -> APIKey | None:
        key_obj = (
            self.db.query(APIKey)
            .filter(APIKey.id == key_id, APIKey.user_id == user_id)
            .first()
        )
        if key_obj is None:
            return None
        key_obj.is_active = False
        self.db.commit()
        self.db.refresh(key_obj)
        return key_obj

    def validate_key(self, raw_key: str) -> APIKey | None:
        """Validate a raw API key. Returns the key object or None."""
        hashed = _hash_key(raw_key)
        key_obj = (
            self.db.query(APIKey)
            .filter(APIKey.key_hash == hashed, APIKey.is_active.is_(True))
            .first()
        )
        if key_obj is None:
            return None
        # Check expiry
        if key_obj.expires_at and key_obj.expires_at < datetime.now(UTC).replace(tzinfo=None):
            return None
        # Update last_used_at
        key_obj.last_used_at = datetime.now(UTC).replace(tzinfo=None)
        self.db.commit()
        return key_obj

    def cleanup_expired_keys(self) -> int:
        """Deactivate all expired API keys. Returns count of deactivated keys."""
        now = datetime.now(UTC).replace(tzinfo=None)
        expired = (
            self.db.query(APIKey)
            .filter(
                APIKey.is_active.is_(True),
                APIKey.expires_at.isnot(None),
                APIKey.expires_at < now,
            )
            .all()
        )
        for key in expired:
            key.is_active = False
        if expired:
            self.db.commit()
        return len(expired)
