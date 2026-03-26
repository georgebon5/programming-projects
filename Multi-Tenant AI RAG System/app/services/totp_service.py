"""
Two-Factor Authentication service using TOTP (RFC 6238).

Flow:
1. User calls POST /auth/2fa/enable  → gets a secret + provisioning URI (for QR code).
2. User scans the QR in an authenticator app and calls POST /auth/2fa/verify with a TOTP code.
3. On login, if 2FA is enabled, the user must provide a totp_code alongside credentials.
4. User can disable 2FA via POST /auth/2fa/disable (requires a valid TOTP code).
"""

import io
import base64
import pyotp
import qrcode
from sqlalchemy.orm import Session

from app.models.user import User


class TwoFactorService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_secret(self, user: User) -> dict:
        """Generate a new TOTP secret and provisioning URI.

        Returns a dict with 'secret' and 'provisioning_uri' (otpauth://...)
        and 'qr_code_base64' for easy frontend rendering.
        """
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="MultiTenantRAG",
        )

        # Generate QR code as base64 PNG
        img = qrcode.make(provisioning_uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()

        # Store secret on user (not yet enabled)
        user.totp_secret = secret
        self.db.commit()

        return {
            "secret": secret,
            "provisioning_uri": provisioning_uri,
            "qr_code_base64": qr_b64,
        }

    def verify_and_enable(self, user: User, code: str) -> bool:
        """Verify a TOTP code and enable 2FA if valid."""
        if not user.totp_secret:
            return False
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(code, valid_window=1):
            user.totp_enabled = True
            self.db.commit()
            return True
        return False

    def verify_code(self, user: User, code: str) -> bool:
        """Verify a TOTP code (for login)."""
        if not user.totp_secret or not user.totp_enabled:
            return False
        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code, valid_window=1)

    def disable(self, user: User, code: str) -> bool:
        """Disable 2FA after verifying the code."""
        if not self.verify_code(user, code):
            return False
        user.totp_secret = None
        user.totp_enabled = False
        self.db.commit()
        return True
