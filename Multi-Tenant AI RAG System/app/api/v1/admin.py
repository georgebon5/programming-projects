"""
Admin-only endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User, UserRole
from app.services.cleanup_service import CleanupService

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/cleanup", status_code=status.HTTP_200_OK)
def run_cleanup(
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> dict:
    """Manually trigger cleanup of expired tokens. Admin only."""
    service = CleanupService(db)
    counts = service.cleanup_expired_tokens()
    return {"detail": "Cleanup completed", "deleted": counts}
