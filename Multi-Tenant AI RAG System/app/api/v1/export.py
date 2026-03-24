"""
GDPR / data export endpoints — users can download all their data.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.audit_log import AuditAction, AuditLog
from app.models.chat import ChatMessage
from app.models.document import Document
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/me", tags=["Account"])


@router.get("/export")
def export_my_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    GDPR Article 20 — Data portability.  Returns all personal data
    associated with the authenticated user in a machine-readable format.
    """
    # Log export action
    audit = AuditService(db)
    audit.log(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=AuditAction.DATA_EXPORT,
        resource_type="user",
        resource_id=str(current_user.id),
    )

    documents = (
        db.query(Document)
        .filter(Document.uploaded_by_id == current_user.id)
        .all()
    )
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == current_user.id)
        .order_by(AuditLog.created_at)
        .all()
    )

    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "username": current_user.username,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "documents": [
            {
                "id": str(d.id),
                "filename": d.original_filename,
                "mime_type": d.mime_type,
                "size_bytes": d.file_size_bytes,
                "status": d.status.value,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in documents
        ],
        "chat_messages": [
            {
                "id": str(m.id),
                "conversation_id": m.conversation_id,
                "role": m.role.value,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "audit_logs": [
            {
                "id": str(a.id),
                "action": a.action.value,
                "resource_type": a.resource_type,
                "resource_id": a.resource_id,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in audit_logs
        ],
    }
