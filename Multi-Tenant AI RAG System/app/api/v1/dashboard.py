"""
Admin dashboard API — tenant stats and recent activity.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User, UserRole
from app.schemas.dashboard import DashboardResponse, RecentActivity, TenantStats
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])


@router.get("/", response_model=DashboardResponse)
def get_dashboard(
    activity_limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Get tenant statistics and recent activity (admin only)."""
    service = DashboardService(db)
    stats = service.get_stats(current_user.tenant_id)
    activity = service.get_recent_activity(current_user.tenant_id, limit=activity_limit)

    return DashboardResponse(
        stats=TenantStats(**stats),
        recent_activity=[RecentActivity(**a) for a in activity],
    )
