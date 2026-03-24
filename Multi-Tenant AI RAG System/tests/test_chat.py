"""
Tests for RAG chat endpoint and conversation history.
"""

import io

from tests.conftest import auth_header, register_tenant


def _setup_tenant_with_doc(client):
    """Helper: register tenant, upload doc, return token."""
    _, token = register_tenant(client)
    content = (
        "Artificial Intelligence is a branch of computer science. "
        "Machine learning is a subset of AI. "
        "Deep learning uses neural networks. "
    ) * 30  # Enough text for chunking
    client.post(
        "/api/v1/documents/upload",
        headers=auth_header(token),
        files={"file": ("ai.txt", io.BytesIO(content.encode()), "text/plain")},
    )
    return token


class TestChat:
    def test_chat_returns_answer(self, client):
        token = _setup_tenant_with_doc(client)
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "What is AI?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "conversation_id" in data
        assert isinstance(data["sources"], list)

    def test_chat_conversation_continuity(self, client):
        token = _setup_tenant_with_doc(client)
        # First message
        r1 = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "What is machine learning?"},
        )
        conv_id = r1.json()["conversation_id"]

        # Follow-up in same conversation
        r2 = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "Tell me more", "conversation_id": conv_id},
        )
        assert r2.status_code == 200
        assert r2.json()["conversation_id"] == conv_id

    def test_chat_no_token(self, client):
        resp = client.post(
            "/api/v1/chat/",
            json={"question": "test"},
        )
        assert resp.status_code == 403

    def test_chat_empty_question(self, client):
        token = _setup_tenant_with_doc(client)
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": ""},
        )
        assert resp.status_code == 422


class TestConversationHistory:
    def test_get_history(self, client):
        token = _setup_tenant_with_doc(client)
        # Send a message
        r = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "What is deep learning?"},
        )
        conv_id = r.json()["conversation_id"]

        # Fetch history
        resp = client.get(
            f"/api/v1/chat/{conv_id}",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        msgs = resp.json()["messages"]
        assert len(msgs) == 2  # user + assistant
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_history_not_found(self, client):
        _, token = register_tenant(client)
        resp = client.get(
            "/api/v1/chat/nonexistent-conv",
            headers=auth_header(token),
        )
        assert resp.status_code == 404


class TestChatTenantIsolation:
    def test_tenant_a_chat_invisible_to_b(self, client):
        """Tenant B cannot access Tenant A's conversations."""
        token_a = _setup_tenant_with_doc(client)
        _, token_b = register_tenant(client)

        # Tenant A chats
        r = client.post(
            "/api/v1/chat/",
            headers=auth_header(token_a),
            json={"question": "Tell me about AI"},
        )
        conv_id = r.json()["conversation_id"]

        # Tenant B tries to access conversation → 404
        resp = client.get(
            f"/api/v1/chat/{conv_id}",
            headers=auth_header(token_b),
        )
        assert resp.status_code == 404
