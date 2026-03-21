from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.utils.security import hash_password, verify_password


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register_tenant_with_admin(
        self,
        *,
        tenant_name: str,
        tenant_slug: str,
        tenant_description: str | None,
        username: str,
        email: str,
        password: str,
    ) -> User:
        existing_tenant = self.db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
        if existing_tenant:
            raise ValueError("Tenant slug already exists")

        tenant = Tenant(
            name=tenant_name,
            slug=tenant_slug,
            description=tenant_description,
            is_active=True,
            subscription_tier="free",
        )
        self.db.add(tenant)
        self.db.flush()

        existing_user = (
            self.db.query(User)
            .filter(User.tenant_id == tenant.id, User.email == email)
            .first()
        )
        if existing_user:
            raise ValueError("User email already exists in tenant")

        user = User(
            tenant_id=tenant.id,
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, *, email: str, password: str) -> User | None:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        user.last_login = datetime.now(UTC).replace(tzinfo=None)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()
