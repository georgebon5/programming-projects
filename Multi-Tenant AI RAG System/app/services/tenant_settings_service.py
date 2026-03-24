"""
Tenant settings service — manage quotas and enforce limits.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage
from app.models.document import Document
from app.models.tenant_settings import TenantSettings
from app.models.user import User


class QuotaExceeded(Exception):
    """Raised when a tenant exceeds a quota limit."""
    pass


class TenantSettingsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, tenant_id: UUID) -> TenantSettings:
        settings = (
            self.db.query(TenantSettings)
            .filter(TenantSettings.tenant_id == tenant_id)
            .first()
        )
        if not settings:
            settings = TenantSettings(tenant_id=tenant_id)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
        return settings

    def update(self, tenant_id: UUID, **kwargs) -> TenantSettings:
        settings = self.get_or_create(tenant_id)
        allowed = {
            "max_users", "max_documents", "max_storage_mb",
            "max_chat_messages_per_day", "chat_enabled", "file_upload_enabled",
        }
        for key, value in kwargs.items():
            if key in allowed and value is not None:
                setattr(settings, key, value)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def check_user_quota(self, tenant_id: UUID) -> None:
        settings = self.get_or_create(tenant_id)
        current = self.db.query(func.count(User.id)).filter(User.tenant_id == tenant_id).scalar() or 0
        if current >= settings.max_users:
            raise QuotaExceeded(f"User limit reached ({settings.max_users})")

    def check_document_quota(self, tenant_id: UUID) -> None:
        settings = self.get_or_create(tenant_id)
        current = self.db.query(func.count(Document.id)).filter(Document.tenant_id == tenant_id).scalar() or 0
        if current >= settings.max_documents:
            raise QuotaExceeded(f"Document limit reached ({settings.max_documents})")

    def check_storage_quota(self, tenant_id: UUID, new_file_bytes: int) -> None:
        settings = self.get_or_create(tenant_id)
        current_bytes = (
            self.db.query(func.coalesce(func.sum(Document.file_size_bytes), 0))
            .filter(Document.tenant_id == tenant_id)
            .scalar()
        )
        max_bytes = settings.max_storage_mb * 1024 * 1024
        if current_bytes + new_file_bytes > max_bytes:
            raise QuotaExceeded(f"Storage limit reached ({settings.max_storage_mb}MB)")

    def check_chat_quota(self, tenant_id: UUID) -> None:
        settings = self.get_or_create(tenant_id)
        if not settings.chat_enabled:
            raise QuotaExceeded("Chat is disabled for this tenant")

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        today_messages = (
            self.db.query(func.count(ChatMessage.id))
            .filter(
                ChatMessage.tenant_id == tenant_id,
                ChatMessage.created_at >= today_start,
            )
            .scalar()
            or 0
        )
        if today_messages >= settings.max_chat_messages_per_day:
            raise QuotaExceeded(f"Daily chat limit reached ({settings.max_chat_messages_per_day})")

    def check_upload_enabled(self, tenant_id: UUID) -> None:
        settings = self.get_or_create(tenant_id)
        if not settings.file_upload_enabled:
            raise QuotaExceeded("File upload is disabled for this tenant")

    def get_usage(self, tenant_id: UUID) -> dict:
        """Get current usage vs. limits."""
        settings = self.get_or_create(tenant_id)

        user_count = self.db.query(func.count(User.id)).filter(User.tenant_id == tenant_id).scalar() or 0
        doc_count = self.db.query(func.count(Document.id)).filter(Document.tenant_id == tenant_id).scalar() or 0
        storage_bytes = (
            self.db.query(func.coalesce(func.sum(Document.file_size_bytes), 0))
            .filter(Document.tenant_id == tenant_id)
            .scalar()
        )

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
        chat_today = (
            self.db.query(func.count(ChatMessage.id))
            .filter(ChatMessage.tenant_id == tenant_id, ChatMessage.created_at >= today_start)
            .scalar()
            or 0
        )

        return {
            "users": {"current": user_count, "limit": settings.max_users},
            "documents": {"current": doc_count, "limit": settings.max_documents},
            "storage_mb": {
                "current": round(storage_bytes / (1024 * 1024), 2),
                "limit": settings.max_storage_mb,
            },
            "chat_messages_today": {
                "current": chat_today,
                "limit": settings.max_chat_messages_per_day,
            },
            "features": {
                "chat_enabled": settings.chat_enabled,
                "file_upload_enabled": settings.file_upload_enabled,
            },
        }
