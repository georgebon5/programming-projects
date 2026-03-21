from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.auth import CurrentUserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user)


@router.get("/admin-only", response_model=dict)
def admin_only(
    current_user: User = Depends(require_role({UserRole.ADMIN})),
) -> dict:
    return {
        "message": "Admin endpoint access granted",
        "user_id": str(current_user.id),
        "tenant_id": str(current_user.tenant_id),
    }
