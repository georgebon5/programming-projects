"""
Tests for:
  - Soft delete: documents excluded from list after delete
  - Restore: soft-deleted doc comes back
  - GET /documents/deleted admin listing
  - Document reprocess endpoint
  - Bulk upload endpoint
"""

import io
import uuid

import pytest

from tests.conftest import auth_header, register_tenant


# ── Helpers ──────────────────────────────────────────────────────────────────

def _upload_txt(client, token, filename="test.txt", content="Hello world. " * 50):
    return client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": (filename, io.BytesIO(content.encode()), "text/plain")},
    )


def _upload_and_get_id(client, token, filename="test.txt"):
    resp = _upload_txt(client, token, filename=filename)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Part A: Soft Delete ───────────────────────────────────────────────────────

class TestSoftDelete:
    def test_deleted_doc_absent_from_list(self, client):
        """After deleting a document it should not appear in list_documents."""
        _, token = register_tenant(client, f"sd-{uuid.uuid4().hex[:6]}")
        doc_id = _upload_and_get_id(client, token)

        # Confirm present
        resp = client.get("/api/v1/documents/", headers=auth_header(token))
        assert resp.json()["total"] == 1

        # Soft-delete
        del_resp = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert del_resp.status_code == 204

        # No longer in list
        resp = client.get("/api/v1/documents/", headers=auth_header(token))
        assert resp.json()["total"] == 0

    def test_deleted_doc_absent_from_get(self, client):
        """GET /{id} returns 404 for a soft-deleted document."""
        _, token = register_tenant(client, f"sd-get-{uuid.uuid4().hex[:6]}")
        doc_id = _upload_and_get_id(client, token)

        client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token))

        resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert resp.status_code == 404

    def test_delete_twice_returns_404(self, client):
        """Deleting an already-deleted document should 404."""
        _, token = register_tenant(client, f"sd-dup-{uuid.uuid4().hex[:6]}")
        doc_id = _upload_and_get_id(client, token)

        client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        resp = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert resp.status_code == 404


# ── Part A: Restore ───────────────────────────────────────────────────────────

class TestRestoreDocument:
    def test_restore_brings_doc_back(self, client):
        """Restoring a soft-deleted doc makes it visible again."""
        _, token = register_tenant(client, f"res-{uuid.uuid4().hex[:6]}")
        doc_id = _upload_and_get_id(client, token)

        # Delete
        client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token)).status_code == 404

        # Restore (admin endpoint)
        resp = client.post(f"/api/v1/documents/{doc_id}/restore", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == doc_id
        assert data["deleted_at"] is None

        # Now visible again
        resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert resp.status_code == 200

    def test_restore_nonexistent_returns_404(self, client):
        _, token = register_tenant(client, f"res-404-{uuid.uuid4().hex[:6]}")
        resp = client.post(f"/api/v1/documents/{uuid.uuid4()}/restore", headers=auth_header(token))
        assert resp.status_code == 404

    def test_restore_non_deleted_doc_returns_404(self, client):
        """Trying to restore a document that was never deleted should 404."""
        _, token = register_tenant(client, f"res-nd-{uuid.uuid4().hex[:6]}")
        doc_id = _upload_and_get_id(client, token)
        resp = client.post(f"/api/v1/documents/{doc_id}/restore", headers=auth_header(token))
        assert resp.status_code == 404


# ── Part A: Deleted listing ───────────────────────────────────────────────────

class TestListDeletedDocuments:
    def test_deleted_docs_visible_in_deleted_endpoint(self, client):
        """/documents/deleted lists soft-deleted docs for admin."""
        _, token = register_tenant(client, f"del-list-{uuid.uuid4().hex[:6]}")
        doc_id = _upload_and_get_id(client, token)

        # Initially empty
        resp = client.get("/api/v1/documents/deleted", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

        # Delete
        client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token))

        # Now shows up
        resp = client.get("/api/v1/documents/deleted", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["documents"][0]["id"] == doc_id
        assert data["documents"][0]["deleted_at"] is not None

    def test_deleted_listing_empty_when_none_deleted(self, client):
        _, token = register_tenant(client, f"del-empty-{uuid.uuid4().hex[:6]}")
        _upload_and_get_id(client, token)  # upload but don't delete
        resp = client.get("/api/v1/documents/deleted", headers=auth_header(token))
        assert resp.json()["total"] == 0

    def test_viewer_cannot_access_deleted_list(self, client):
        _, admin_tok = register_tenant(client, f"del-perm-{uuid.uuid4().hex[:6]}")
        viewer_email = f"viewer-{uuid.uuid4().hex[:6]}@test.com"
        client.post(
            "/api/v1/users/invite",
            headers=auth_header(admin_tok),
            json={"username": "viewer", "email": viewer_email, "password": "Password1234!", "role": "viewer"},
        )
        login = client.post("/api/v1/auth/login", json={"email": viewer_email, "password": "Password1234!"})
        viewer_tok = login.json()["access_token"]
        resp = client.get("/api/v1/documents/deleted", headers=auth_header(viewer_tok))
        assert resp.status_code == 403


# ── Part B: Reprocess ─────────────────────────────────────────────────────────

class TestReprocessDocument:
    def test_reprocess_completed_doc(self, client):
        """Reprocessing a completed doc should return a completed doc."""
        _, token = register_tenant(client, f"rep-{uuid.uuid4().hex[:6]}")
        doc_id = _upload_and_get_id(client, token)

        # Ensure it's completed (background task runs synchronously in TestClient)
        get_resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token))
        assert get_resp.json()["status"] == "completed"

        resp = client.post(f"/api/v1/documents/{doc_id}/reprocess", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == doc_id
        assert data["status"] == "completed"
        assert data["total_chunks"] >= 1

    def test_reprocess_nonexistent_doc_returns_404(self, client):
        _, token = register_tenant(client, f"rep-404-{uuid.uuid4().hex[:6]}")
        resp = client.post(f"/api/v1/documents/{uuid.uuid4()}/reprocess", headers=auth_header(token))
        assert resp.status_code == 404

    def test_reprocess_processing_doc_returns_422(self, client, db):
        """Cannot reprocess a document that is currently being processed."""
        from app.models.document import Document, DocumentStatus

        _, token = register_tenant(client, f"rep-422-{uuid.uuid4().hex[:6]}")
        doc_id = _upload_and_get_id(client, token)

        # Force status to PROCESSING via the shared test DB session
        doc = db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
        assert doc is not None
        doc.status = DocumentStatus.PROCESSING
        db.commit()

        resp = client.post(f"/api/v1/documents/{doc_id}/reprocess", headers=auth_header(token))
        assert resp.status_code == 422


# ── Part C: Bulk Upload ───────────────────────────────────────────────────────

class TestBulkUpload:
    def test_bulk_upload_creates_multiple_docs(self, client):
        """Bulk upload of 3 files should create 3 documents."""
        _, token = register_tenant(client, f"bulk-{uuid.uuid4().hex[:6]}")
        files = [
            ("files", (f"file{i}.txt", io.BytesIO(f"Content of file {i}. ".encode() * 50), "text/plain"))
            for i in range(3)
        ]
        resp = client.post(
            "/api/v1/documents/bulk",
            headers=auth_header(token),
            files=files,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert len(data) == 3
        filenames = {d["original_filename"] for d in data}
        assert filenames == {"file0.txt", "file1.txt", "file2.txt"}

    def test_bulk_upload_exceeding_limit_returns_400(self, client):
        """More than 10 files should be rejected."""
        _, token = register_tenant(client, f"bulk-lim-{uuid.uuid4().hex[:6]}")
        files = [
            ("files", (f"f{i}.txt", io.BytesIO(b"x" * 10), "text/plain"))
            for i in range(11)
        ]
        resp = client.post(
            "/api/v1/documents/bulk",
            headers=auth_header(token),
            files=files,
        )
        assert resp.status_code == 400
        assert "Maximum 10" in resp.json()["detail"]

    def test_bulk_upload_invalid_file_type_rejected(self, client):
        """A batch containing a disallowed file type should be rejected entirely."""
        _, token = register_tenant(client, f"bulk-bad-{uuid.uuid4().hex[:6]}")
        files = [
            ("files", ("good.txt", io.BytesIO(b"hello"), "text/plain")),
            ("files", ("bad.exe", io.BytesIO(b"MZ"), "application/octet-stream")),
        ]
        resp = client.post(
            "/api/v1/documents/bulk",
            headers=auth_header(token),
            files=files,
        )
        assert resp.status_code == 400

    def test_bulk_upload_shows_in_list(self, client):
        """Bulk-uploaded documents should appear in the standard list."""
        _, token = register_tenant(client, f"bulk-list-{uuid.uuid4().hex[:6]}")
        files = [
            ("files", (f"doc{i}.txt", io.BytesIO(f"Doc {i} content. ".encode() * 30), "text/plain"))
            for i in range(2)
        ]
        client.post("/api/v1/documents/bulk", headers=auth_header(token), files=files)

        resp = client.get("/api/v1/documents/", headers=auth_header(token))
        assert resp.json()["total"] == 2

    def test_viewer_cannot_bulk_upload(self, client):
        _, admin_tok = register_tenant(client, f"bulk-perm-{uuid.uuid4().hex[:6]}")
        viewer_email = f"viewer-{uuid.uuid4().hex[:6]}@test.com"
        client.post(
            "/api/v1/users/invite",
            headers=auth_header(admin_tok),
            json={"username": "viewer", "email": viewer_email, "password": "Password1234!", "role": "viewer"},
        )
        login = client.post("/api/v1/auth/login", json={"email": viewer_email, "password": "Password1234!"})
        viewer_tok = login.json()["access_token"]
        files = [("files", ("x.txt", io.BytesIO(b"hello"), "text/plain"))]
        resp = client.post("/api/v1/documents/bulk", headers=auth_header(viewer_tok), files=files)
        assert resp.status_code == 403
