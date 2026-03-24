from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.utils.exceptions import AccountLockedError, PasswordValidationError
from app.utils.security import hash_password, validate_password_strength, verify_password

# In-memory login attempt tracker  {email: (failed_count, last_attempt_time)}
_login_attempts: dict[str, tuple[int, datetime]] = {}


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _check_account_lockout(self, email: str) -> None:
        """Raise AccountLockedError if too many recent failed attempts."""
        record = _login_attempts.get(email)
        if record is None:
            return
        failed_count, last_attempt = record
        if failed_count >= settings.max_login_attempts:
            lockout_until = last_attempt + timedelta(minutes=settings.login_lockout_minutes)
            if datetime.now(UTC) < lockout_until.replace(tzinfo=UTC if lockout_until.tzinfo is None else lockout_until.tzinfo):
                raise AccountLockedError(
                    f"Account temporarily locked due to {failed_count} failed login attempts. "
                    f"Try again in {settings.login_lockout_minutes} minutes."
                )
            # Lockout expired — reset
            _login_attempts.pop(email, None)

    def _record_failed_login(self, email: str) -> None:
        record = _login_attempts.get(email)
        if record:
            _login_attempts[email] = (record[0] + 1, datetime.now(UTC).replace(tzinfo=None))
        else:
            _login_attempts[email] = (1, datetime.now(UTC).replace(tzinfo=None))

    def _clear_failed_logins(self, email: str) -> None:
        _login_attempts.pop(email, None)

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
