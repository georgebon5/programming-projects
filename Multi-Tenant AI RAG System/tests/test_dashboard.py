"""
Tests for admin dashboard endpoint.
"""

import io

from tests.conftest import auth_header, register_tenant


class TestDashboard:
    def test_dashboard_admin_access(self, client):
        _, token = register_tenant(client, "dash-admin")

        # Seed one document + one chat for stats
        upload_content = ("Dashboard test content. " * 80).encode()
        client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={"file": ("dash.txt", io.BytesIO(upload_content), "text/plain")},
        )
        client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "What is in my doc?"},
        )

        resp = client.get("/api/v1/admin/dashboard/", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["stats"]["total_users"] >= 1
        assert data["stats"]["total_documents"] >= 1
        assert data["stats"]["total_messages"] >= 2
        assert isinstance(data["recent_activity"], list)

    def test_dashboard_viewer_forbidden(self, client):
        _, admin_token = register_tenant(client, "dash-view")

        # Create viewer
        client.post(
            "/api/v1/users/invite",
            headers=auth_header(admin_token),
            json={
                "username": "viewer",
                "email": "viewer@dash-view.com",
                "password": "Password1234!",
                "role": "viewer",
            },
        )

        login = client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@dash-view.com", "password": "Password1234!"},
        )
        viewer_token = login.json()["access_token"]

        resp = client.get("/api/v1/admin/dashboard/", headers=auth_header(viewer_token))
        assert resp.status_code == 403
