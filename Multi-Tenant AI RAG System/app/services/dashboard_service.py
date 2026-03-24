"""
Admin dashboard service — aggregate tenant stats and recent activity.
"""

from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage
from app.models.document import Document, DocumentStatus
from app.models.tenant import Tenant
from app.models.user import User


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_stats(self, tenant_id: UUID) -> dict:
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()

        total_users = self.db.query(func.count(User.id)).filter(User.tenant_id == tenant_id).scalar() or 0
        active_users = (
            self.db.query(func.count(User.id))
            .filter(User.tenant_id == tenant_id, User.is_active.is_(True))
            .scalar()
            or 0
        )

        total_docs = self.db.query(func.count(Document.id)).filter(Document.tenant_id == tenant_id).scalar() or 0
        processed_docs = (
            self.db.query(func.count(Document.id))
            .filter(Document.tenant_id == tenant_id, Document.status == DocumentStatus.COMPLETED)
            .scalar()
            or 0
        )
        failed_docs = (
            self.db.query(func.count(Document.id))
            .filter(Document.tenant_id == tenant_id, Document.status == DocumentStatus.FAILED)
            .scalar()
            or 0
        )

        total_chunks = (
            self.db.query(func.coalesce(func.sum(Document.total_chunks), 0))
            .filter(Document.tenant_id == tenant_id)
            .scalar()
        )

        total_conversations = (
            self.db.query(func.count(func.distinct(ChatMessage.conversation_id)))
            .filter(ChatMessage.tenant_id == tenant_id)
            .scalar()
            or 0
        )
        total_messages = (
            self.db.query(func.count(ChatMessage.id))
            .filter(ChatMessage.tenant_id == tenant_id)
            .scalar()
            or 0
        )

        storage_bytes = (
            self.db.query(func.coalesce(func.sum(Document.file_size_bytes), 0))
            .filter(Document.tenant_id == tenant_id)
            .scalar()
        )

        return {
            "tenant_name": tenant.name if tenant else "Unknown",
            "total_users": total_users,
            "active_users": active_users,
            "total_documents": total_docs,
            "processed_documents": processed_docs,
            "failed_documents": failed_docs,
            "total_chunks": total_chunks,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "storage_bytes": storage_bytes,
        }

    def get_recent_activity(self, tenant_id: UUID, limit: int = 10) -> list[dict]:
        activities: list[dict] = []

        # Recent uploads
        recent_docs = (
            self.db.query(Document)
            .filter(Document.tenant_id == tenant_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .all()
        )
        for doc in recent_docs:
            activities.append({
                "type": "upload",
                "description": f"Document '{doc.original_filename}' uploaded ({doc.status.value})",
                "timestamp": doc.created_at,
            })

        # Recent chats (one per conversation)
        recent_convs = (
            self.db.query(
                ChatMessage.conversation_id,
                func.min(ChatMessage.content).label("first_msg"),
                func.max(ChatMessage.created_at).label("last_at"),
            )
            .filter(ChatMessage.tenant_id == tenant_id)
            .group_by(ChatMessage.conversation_id)
            .order_by(func.max(ChatMessage.created_at).desc())
            .limit(limit)
            .all()
        )
        for conv in recent_convs:
            preview = (conv.first_msg or "")[:80]
            activities.append({
                "type": "chat",
                "description": f"Conversation: \"{preview}...\"",
                "timestamp": conv.last_at,
            })

        # Recent users
        recent_users = (
            self.db.query(User)
            .filter(User.tenant_id == tenant_id)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )
        for u in recent_users:
            activities.append({
                "type": "user_joined",
                "description": f"{u.username} ({u.email}) joined as {u.role.value}",
                "timestamp": u.created_at,
            })

        # Sort by timestamp descending, return top N
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        return activities[:limit]
