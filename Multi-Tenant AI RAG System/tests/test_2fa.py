"""
Tests για 2FA (TOTP): enable, verify, login με 2FA, disable.
"""

import pytest
from tests.conftest import auth_header, register_tenant

class TestTwoFactorAuth:
    def test_enable_2fa_flow(self, client):
        # 1. Register tenant/admin
        user, token = register_tenant(client, "2fa")
        headers = auth_header(token)

        # 2. Enable 2FA (get secret, provisioning_uri, qr_code_base64)
        resp = client.post("/api/v1/auth/2fa/enable", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "secret" in data and "provisioning_uri" in data and "qr_code_base64" in data
        secret = data["secret"]

        # 3. Generate valid TOTP code
        import pyotp
        totp = pyotp.TOTP(secret)
        code = totp.now()

        # 4. Verify 2FA (activate)
        verify_resp = client.post(
            "/api/v1/auth/2fa/verify",
            json={"code": code},
            headers=headers,
        )
        assert verify_resp.status_code == 200
        assert verify_resp.json()["detail"].startswith("Two-factor authentication enabled")

        # 5. Τώρα το login ΧΩΡΙΣ TOTP code πρέπει να απορρίπτεται
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": "Password1234!"},
        )
        assert login_resp.status_code == 401
        assert login_resp.json()["detail"] == "2FA code required"

        # 6. Login με σωστό TOTP code
        login_2fa = client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": "Password1234!", "totp_code": totp.now()},
        )
        assert login_2fa.status_code == 200
        assert "access_token" in login_2fa.json()

        # 7. Disable 2FA
        disable_resp = client.post(
            "/api/v1/auth/2fa/disable",
            json={"code": totp.now()},
            headers=auth_header(login_2fa.json()["access_token"]),
        )
        assert disable_resp.status_code == 200
        assert "disabled" in disable_resp.json()["detail"]

        # 8. Login again (should NOT require 2FA)
        login_no_2fa = client.post(
            "/api/v1/auth/login",
            json={"email": user["email"], "password": "Password1234!"},
        )
        assert login_no_2fa.status_code == 200
        assert "access_token" in login_no_2fa.json()
