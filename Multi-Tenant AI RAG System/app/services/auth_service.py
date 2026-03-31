from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.login_attempt import LoginAttempt
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.utils.exceptions import AccountLockedError, PasswordValidationError
from app.utils.security import hash_password, validate_password_strength, verify_password


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Account lockout (DB-persistent) ──────────────────────────────────

    def _check_account_lockout(self, email: str) -> None:
        """Raise AccountLockedError if too many recent failed attempts."""
        record = self.db.query(LoginAttempt).filter(LoginAttempt.email == email).first()
        if record is None:
            return
        if record.locked_until and datetime.now(UTC).replace(tzinfo=None) < record.locked_until:
            raise AccountLockedError(
                f"Account temporarily locked due to {record.failed_count} failed login attempts. "
                f"Try again in {settings.login_lockout_minutes} minutes."
            )
        # Lockout expired — reset
        if record.locked_until:
            record.failed_count = 0
            record.locked_until = None
            self.db.commit()

    def _record_failed_login(self, email: str) -> None:
        record = self.db.query(LoginAttempt).filter(LoginAttempt.email == email).first()
        now = datetime.now(UTC).replace(tzinfo=None)
        if record:
            record.failed_count += 1
            record.last_failed_at = now
            if record.failed_count >= settings.max_login_attempts:
                record.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
        else:
            record = LoginAttempt(email=email, failed_count=1, last_failed_at=now)
            self.db.add(record)
        self.db.commit()

    def _clear_failed_logins(self, email: str) -> None:
        self.db.query(LoginAttempt).filter(LoginAttempt.email == email).delete()
        self.db.commit()

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
        # Validate password complexity
        validate_password_strength(password)

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
        # Check lockout before attempting authentication
        self._check_account_lockout(email)

        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            self._record_failed_login(email)
            return None

        if not user.is_active:
            self._record_failed_login(email)
            return None

        if not verify_password(password, user.hashed_password):
            self._record_failed_login(email)
            return None

        # Successful login — clear any failed attempts
        self._clear_failed_logins(email)

        user.last_login = datetime.now(UTC).replace(tzinfo=None)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()
