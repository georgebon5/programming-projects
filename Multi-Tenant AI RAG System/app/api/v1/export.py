"""
GDPR / data export and account deletion endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import get_current_user
from app.models.audit_log import AuditAction, AuditLog
from app.models.chat import ChatMessage
from app.models.document import Document
from app.models.user import User
from app.services.audit_service import AuditService
from app.utils.security import verify_password

router = APIRouter(prefix="/me", tags=["Account"])


class DeleteAccountRequest(BaseModel):
    password: str


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


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    GDPR Article 17 — Right to erasure.

    Permanently deletes the authenticated user's account and all associated
    personal data (chat messages, login attempts, sessions).

    Documents uploaded by this user remain visible to the tenant — they were
    created in the context of the organization, not the individual.

    Requires the current password to prevent accidental or unauthorized deletion.
    Audit log entries are retained but de-linked (user_id set to NULL).
    """
    if not verify_password(payload.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incorrect password.",
        )

    user_id = current_user.id
    tenant_id = current_user.tenant_id

    # Record deletion before the user row is gone so the log entry is committed
    AuditService(db).log(
        tenant_id=tenant_id,
        user_id=user_id,
        action=AuditAction.ACCOUNT_DELETE,
        resource_type="user",
        resource_id=str(user_id),
    )

    # Delete personal chat history
    db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete(
        synchronize_session=False
    )

    # Delete the user — FK cascade SET NULL on audit_logs preserves the trail
    db.delete(current_user)
    db.commit()
