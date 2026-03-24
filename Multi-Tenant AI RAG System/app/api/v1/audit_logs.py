"""
Audit log API — view audit trail (admin only).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import require_role
from app.models.audit_log import AuditAction
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin/audit-logs", tags=["Admin Audit Logs"])


@router.get("/", response_model=AuditLogListResponse)
def list_audit_logs(
    action: AuditAction | None = None,
    user_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    """List audit logs for the tenant. Filterable by action and user."""
    service = AuditService(db)
    logs, total = service.list_logs(
        tenant_id=current_user.tenant_id,
        action=action,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )
    return AuditLogListResponse(
        logs=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
    )
