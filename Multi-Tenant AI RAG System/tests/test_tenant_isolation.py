"""
Integration tests for multi-tenant data isolation.

Verifies that tenants are strictly isolated:
- Documents, conversations, users of Tenant A are invisible to Tenant B.
- Tenant B's RAG search never returns Tenant A's vector chunks.
"""

import io

from tests.conftest import auth_header, register_tenant


def _upload_doc(client, token: str, text: str = "generic document content for testing") -> dict:
    """Upload a plain-text document and return the response JSON."""
    content = (text + " ") * 50  # Enough text for chunking
    resp = client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": ("test.txt", io.BytesIO(content.encode()), "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── Document isolation ─────────────────────────────────────────────────────────

class TestDocumentIsolation:
    def test_tenant_b_cannot_see_tenant_a_documents(self, client):
        _, token_a = register_tenant(client, "iso-docs-a")
        _, token_b = register_tenant(client, "iso-docs-b")

        doc = _upload_doc(client, token_a)
        doc_id = doc["id"]

        resp = client.get("/api/v1/documents/", headers=auth_header(token_b))
        assert resp.status_code == 200
        ids = [d["id"] for d in resp.json()["documents"]]
        assert doc_id not in ids

    def test_tenant_b_cannot_fetch_tenant_a_document(self, client):
        _, token_a = register_tenant(client, "iso-fetch-a")
        _, token_b = register_tenant(client, "iso-fetch-b")

        doc = _upload_doc(client, token_a)
        doc_id = doc["id"]

        resp = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token_b))
        assert resp.status_code == 404

    def test_tenant_b_cannot_delete_tenant_a_document(self, client):
        _, token_a = register_tenant(client, "iso-del-a")
        _, token_b = register_tenant(client, "iso-del-b")

        doc = _upload_doc(client, token_a)
        doc_id = doc["id"]

        resp = client.delete(f"/api/v1/documents/{doc_id}", headers=auth_header(token_b))
        assert resp.status_code == 404

        # Still accessible by Tenant A
        resp_a = client.get(f"/api/v1/documents/{doc_id}", headers=auth_header(token_a))
        assert resp_a.status_code == 200

    def test_tenant_b_cannot_trigger_reprocess_of_tenant_a_document(self, client):
        _, token_a = register_tenant(client, "iso-proc-a")
        _, token_b = register_tenant(client, "iso-proc-b")

        doc = _upload_doc(client, token_a)
        doc_id = doc["id"]

        resp = client.post(
            f"/api/v1/documents/{doc_id}/process",
            headers=auth_header(token_b),
        )
        assert resp.status_code == 404

    def test_each_tenant_only_sees_own_documents(self, client):
        _, token_a = register_tenant(client, "iso-own-a")
        _, token_b = register_tenant(client, "iso-own-b")

        doc_a = _upload_doc(client, token_a, text="tenant A exclusive content")
        doc_b = _upload_doc(client, token_b, text="tenant B exclusive content")

        list_a = client.get("/api/v1/documents/", headers=auth_header(token_a)).json()["documents"]
        list_b = client.get("/api/v1/documents/", headers=auth_header(token_b)).json()["documents"]

        ids_a = {d["id"] for d in list_a}
        ids_b = {d["id"] for d in list_b}

        assert doc_a["id"] in ids_a
        assert doc_b["id"] not in ids_a
        assert doc_b["id"] in ids_b
        assert doc_a["id"] not in ids_b


# ── Vector / RAG isolation ─────────────────────────────────────────────────────

class TestVectorIsolation:
    def test_tenant_b_chat_does_not_return_tenant_a_chunks(self, client):
        """Tenant B's RAG search must not include Tenant A's document chunks."""
        _, token_a = register_tenant(client, "iso-vec-a")
        _, token_b = register_tenant(client, "iso-vec-b")

        unique_text = "xyzzy_unique_sentinel_9f3a2c isolation_test_vector_store"
        _upload_doc(client, token_a, text=unique_text)

        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token_b),
            json={"question": unique_text},
        )
        assert resp.status_code == 200
        sources = resp.json()["sources"]
        for src in sources:
            assert unique_text not in (src.get("text") or ""), (
                f"Tenant B received Tenant A's chunk in sources: {src}"
            )

    def test_tenant_a_and_b_have_separate_search_spaces(self, client):
        """Each tenant's search returns only their own content."""
        _, token_a = register_tenant(client, "iso-search-a")
        _, token_b = register_tenant(client, "iso-search-b")

        _upload_doc(client, token_a, text="alpha_exclusive_content_for_tenant_a")
        _upload_doc(client, token_b, text="beta_exclusive_content_for_tenant_b")

        # Tenant A searches for B's content
        resp_a = client.post(
            "/api/v1/chat/",
            headers=auth_header(token_a),
            json={"question": "beta_exclusive_content_for_tenant_b"},
        )
        assert resp_a.status_code == 200
        for src in resp_a.json()["sources"]:
            assert "beta_exclusive" not in (src.get("text") or "")

        # Tenant B searches for A's content
        resp_b = client.post(
            "/api/v1/chat/",
            headers=auth_header(token_b),
            json={"question": "alpha_exclusive_content_for_tenant_a"},
        )
        assert resp_b.status_code == 200
        for src in resp_b.json()["sources"]:
            assert "alpha_exclusive" not in (src.get("text") or "")


# ── Conversation isolation ─────────────────────────────────────────────────────

class TestConversationIsolation:
    def test_tenant_b_cannot_read_tenant_a_conversation(self, client):
        _, token_a = register_tenant(client, "iso-conv-read-a")
        _, token_b = register_tenant(client, "iso-conv-read-b")

        r = client.post(
            "/api/v1/chat/",
            headers=auth_header(token_a),
            json={"question": "Secret question from A"},
        )
        conv_id = r.json()["conversation_id"]

        resp = client.get(f"/api/v1/chat/{conv_id}", headers=auth_header(token_b))
        assert resp.status_code == 404

    def test_tenant_b_list_does_not_include_tenant_a_conversations(self, client):
        _, token_a = register_tenant(client, "iso-conv-list-a")
        _, token_b = register_tenant(client, "iso-conv-list-b")

        client.post(
            "/api/v1/chat/",
            headers=auth_header(token_a),
            json={"question": "Tenant A only question"},
        )

        resp = client.get("/api/v1/chat/", headers=auth_header(token_b))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_tenant_b_cannot_delete_tenant_a_conversation(self, client):
        _, token_a = register_tenant(client, "iso-conv-del-a")
        _, token_b = register_tenant(client, "iso-conv-del-b")

        r = client.post(
            "/api/v1/chat/",
            headers=auth_header(token_a),
            json={"question": "A's question"},
        )
        conv_id = r.json()["conversation_id"]

        resp = client.delete(f"/api/v1/chat/{conv_id}", headers=auth_header(token_b))
        assert resp.status_code == 404

        # Confirm still exists for Tenant A
        resp_a = client.get(f"/api/v1/chat/{conv_id}", headers=auth_header(token_a))
        assert resp_a.status_code == 200


# ── User isolation ─────────────────────────────────────────────────────────────

class TestUserIsolation:
    def test_tenant_a_user_list_excludes_tenant_b_users(self, client):
        _, token_a = register_tenant(client, "iso-usr-a")
        user_b, _ = register_tenant(client, "iso-usr-b")

        resp = client.get("/api/v1/users/", headers=auth_header(token_a))
        assert resp.status_code == 200
        user_ids = {u["id"] for u in resp.json()}
        assert user_b["id"] not in user_ids

    def test_tenant_a_admin_cannot_delete_tenant_b_user(self, client):
        _, token_a = register_tenant(client, "iso-del-usr-a")
        user_b, _ = register_tenant(client, "iso-del-usr-b")

        resp = client.delete(
            f"/api/v1/users/{user_b['id']}",
            headers=auth_header(token_a),
        )
        assert resp.status_code in (403, 404)
