from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.utils.exceptions import UserNotFound
from app.utils.security import hash_password, verify_password


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def invite_user(
        self,
        *,
        tenant_id: UUID,
        username: str,
        email: str,
        password: str,
        role: UserRole = UserRole.MEMBER,
    ) -> User:
        existing = (
            self.db.query(User)
            .filter(User.tenant_id == tenant_id, User.email == email)
            .first()
        )
        if existing:
            raise ValueError("User with this email already exists in tenant")

        user = User(
            tenant_id=tenant_id,
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_tenant_users(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[User], int]:
        query = self.db.query(User).filter(User.tenant_id == tenant_id)
        total = query.count()
        users = query.offset(skip).limit(limit).all()
        return users, total

    def get_user(self, user_id: UUID, tenant_id: UUID) -> User:
        user = (
            self.db.query(User)
            .filter(User.id == user_id, User.tenant_id == tenant_id)
            .first()
        )
        if not user:
            raise UserNotFound("User not found")
        return user

    def update_user(
        self,
        user_id: UUID,
        tenant_id: UUID,
        *,
        username: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> User:
        user = self.get_user(user_id, tenant_id)

        if username is not None:
            user.username = username
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: UUID, tenant_id: UUID) -> None:
        user = self.get_user(user_id, tenant_id)
        self.db.delete(user)
        self.db.commit()

    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        self.db.commit()
