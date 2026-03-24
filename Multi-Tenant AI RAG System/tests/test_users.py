"""
Tests for user management endpoints: invite, list, update, delete, change password.
"""

from tests.conftest import auth_header, register_tenant


class TestInviteUser:
    def test_invite_success(self, client):
        _, token = register_tenant(client, "inv")
        resp = client.post(
            "/api/v1/users/invite",
            headers=auth_header(token),
            json={
                "username": "member1",
                "email": "member1@inv.com",
                "password": "password1234",
                "role": "member",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "member"

    def test_invite_duplicate_email(self, client):
        _, token = register_tenant(client, "inv-dup")
        client.post(
            "/api/v1/users/invite",
            headers=auth_header(token),
            json={
                "username": "m1",
                "email": "same@inv-dup.com",
                "password": "password1234",
            },
        )
        resp = client.post(
            "/api/v1/users/invite",
            headers=auth_header(token),
            json={
                "username": "m2",
                "email": "same@inv-dup.com",
                "password": "password1234",
            },
        )
        assert resp.status_code in (400, 422)

    def test_invite_viewer_cannot_invite(self, client):
        """Only admins can invite users."""
        _, admin_token = register_tenant(client, "inv-perm")
        # Invite a viewer
        resp = client.post(
            "/api/v1/users/invite",
            headers=auth_header(admin_token),
            json={
                "username": "viewer",
                "email": "viewer@inv-perm.com",
                "password": "password1234",
                "role": "viewer",
            },
        )
        assert resp.status_code == 201

        # Login as viewer
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@inv-perm.com", "password": "password1234"},
        )
        viewer_token = login.json()["access_token"]

        # Viewer tries to invite → 403
        resp = client.post(
            "/api/v1/users/invite",
            headers=auth_header(viewer_token),
            json={
                "username": "hack",
                "email": "hack@inv-perm.com",
                "password": "password1234",
            },
        )
        assert resp.status_code == 403


class TestListUsers:
    def test_list_users(self, client):
        _, token = register_tenant(client, "lst")
        # Invite extra user
        client.post(
            "/api/v1/users/invite",
            headers=auth_header(token),
            json={
                "username": "extra",
                "email": "extra@lst.com",
                "password": "password1234",
            },
        )
        resp = client.get("/api/v1/users/", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 2


class TestUpdateUser:
    def test_update_user_role(self, client):
        _, token = register_tenant(client, "upd")
        # Invite member
        invite = client.post(
            "/api/v1/users/invite",
            headers=auth_header(token),
            json={
                "username": "mem",
                "email": "mem@upd.com",
                "password": "password1234",
            },
        )
        user_id = invite.json()["id"]

        # Promote to admin
        resp = client.patch(
            f"/api/v1/users/{user_id}",
            headers=auth_header(token),
            json={"role": "admin"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "admin"

    def test_deactivate_user(self, client):
        _, token = register_tenant(client, "deact")
        invite = client.post(
            "/api/v1/users/invite",
            headers=auth_header(token),
            json={
                "username": "victim",
                "email": "victim@deact.com",
                "password": "password1234",
            },
        )
        user_id = invite.json()["id"]

        resp = client.patch(
            f"/api/v1/users/{user_id}",
            headers=auth_header(token),
            json={"is_active": False},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False


class TestDeleteUser:
    def test_delete_user(self, client):
        _, token = register_tenant(client, "del")
        invite = client.post(
            "/api/v1/users/invite",
            headers=auth_header(token),
            json={
                "username": "delme",
                "email": "delme@del.com",
                "password": "password1234",
            },
        )
        user_id = invite.json()["id"]

        resp = client.delete(f"/api/v1/users/{user_id}", headers=auth_header(token))
        assert resp.status_code == 204

    def test_cannot_delete_self(self, client):
        user, token = register_tenant(client, "nodelete")
        resp = client.delete(
            f"/api/v1/users/{user['id']}",
            headers=auth_header(token),
        )
        assert resp.status_code == 400


class TestChangePassword:
    def test_change_password_success(self, client):
        _, token = register_tenant(client, "pw")
        resp = client.put(
            "/api/v1/users/me/password",
            headers=auth_header(token),
            json={
                "current_password": "password1234",
                "new_password": "newpassword1234",
            },
        )
        assert resp.status_code == 204

        # Verify old password no longer works
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@pw.com", "password": "password1234"},
        )
        assert resp.status_code == 401

        # Verify new password works
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@pw.com", "password": "newpassword1234"},
        )
        assert resp.status_code == 200

    def test_change_password_wrong_current(self, client):
        _, token = register_tenant(client, "pw-bad")
        resp = client.put(
            "/api/v1/users/me/password",
            headers=auth_header(token),
            json={
                "current_password": "wrongcurrentpw",
                "new_password": "newpassword1234",
            },
        )
        assert resp.status_code == 400
