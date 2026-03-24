"""
Tests for document upload, listing, processing, and deletion.
"""

import io

from tests.conftest import auth_header, register_tenant


def _upload_txt(client, token, filename="test.txt", content="Hello world. " * 50):
    """Helper: upload a plain text file."""
    return client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": (filename, io.BytesIO(content.encode()), "text/plain")},
    )


class TestUploadDocument:
    def test_upload_txt(self, client):
        _, token = register_tenant(client, "doc-up")
        resp = _upload_txt(client, token)
        assert resp.status_code == 201
        data = resp.json()
        assert data["original_filename"] == "test.txt"
        # Upload now returns immediately; processing runs in background
        assert data["status"] == "uploaded"

        # Background task runs synchronously in TestClient, so fetching
        # the document should show it as completed.
        doc_id = data["id"]
        get_resp = client.get(
            f"/api/v1/documents/{doc_id}",
            headers=auth_header(token),
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "completed"
        assert get_resp.json()["total_chunks"] >= 1

    def test_upload_unsupported_type(self, client):
        _, token = register_tenant(client, "doc-bad")
        resp = client.post(
            "/api/v1/documents/upload",
            headers=auth_header(token),
            files={
                "file": ("virus.exe", io.BytesIO(b"MZ..."), "application/octet-stream")
            },
        )
        assert resp.status_code == 400

    def test_viewer_cannot_upload(self, client):
        _, admin_token = register_tenant(client, "doc-perm")
        # Create viewer
        client.post(
            "/api/v1/users/invite",
            headers=auth_header(admin_token),
            json={
                "username": "viewer",
                "email": "viewer@doc-perm.com",
                "password": "password1234",
                "role": "viewer",
            },
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": "viewer@doc-perm.com", "password": "password1234"},
        )
        viewer_token = login.json()["access_token"]
        resp = _upload_txt(client, viewer_token)
        assert resp.status_code == 403


class TestListDocuments:
    def test_list_empty(self, client):
        _, token = register_tenant(client, "doc-empty")
        resp = client.get("/api/v1/documents/", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_after_upload(self, client):
        _, token = register_tenant(client, "doc-list")
        _upload_txt(client, token)
        _upload_txt(client, token, filename="second.txt")
        resp = client.get("/api/v1/documents/", headers=auth_header(token))
        assert resp.json()["total"] == 2


class TestGetDocument:
    def test_get_document(self, client):
        _, token = register_tenant(client, "doc-get")
        upload = _upload_txt(client, token)
        doc_id = upload.json()["id"]
        resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == doc_id

    def test_get_document_not_found(self, client):
        _, token = register_tenant(client, "doc-404")
        import uuid

        resp = client.get(
            f"/api/v1/documents/{uuid.uuid4()}", headers=auth_header(token)
        )
        assert resp.status_code == 404


class TestDeleteDocument:
    def test_delete_document(self, client):
        _, token = register_tenant(client, "doc-del")
        upload = _upload_txt(client, token)
        doc_id = upload.json()["id"]
        resp = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert resp.status_code == 204

        # Verify it's gone
        resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert resp.status_code == 404


class TestTenantIsolation:
    def test_tenant_cannot_see_other_docs(self, client):
        """Tenant A's documents are invisible to Tenant B."""
        _, token_a = register_tenant(client, "iso-a")
        _, token_b = register_tenant(client, "iso-b")

        # Tenant A uploads
        upload = _upload_txt(client, token_a, content="Secret of Tenant A. " * 50)
        doc_id = upload.json()["id"]

        # Tenant B cannot see it
        resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token_b))
        assert resp.status_code == 404

        # Tenant B's list is empty
        resp = client.get("/api/v1/documents/", headers=auth_header(token_b))
        assert resp.json()["total"] == 0
