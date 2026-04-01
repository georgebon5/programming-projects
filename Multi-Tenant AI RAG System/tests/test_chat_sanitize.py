"""Integration tests: input sanitization for chat endpoints."""
import pytest

from tests.conftest import auth_header, register_tenant


def _setup_tenant(client):
    """Register a tenant and return the auth token."""
    _, token = register_tenant(client)
    return token


class TestChatSanitization:
    def test_html_tag_only_question_rejected(self, client):
        """A question of empty tags becomes empty after stripping and is rejected (400)."""
        token = _setup_tenant(client)
        # "<b></b>" → "" after stripping → ValueError → 400
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "<b></b>"},
        )
        assert resp.status_code in (400, 422)

    def test_oversized_question_rejected(self, client):
        """Questions exceeding schema max_length (10000) are rejected by Pydantic."""
        token = _setup_tenant(client)
        oversized = "a" * 10001
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": oversized},
        )
        assert resp.status_code == 422

    def test_empty_question_rejected(self, client):
        """Empty question is rejected at schema level."""
        token = _setup_tenant(client)
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": ""},
        )
        assert resp.status_code == 422

    def test_whitespace_only_question_rejected(self, client):
        """Whitespace-only question is rejected."""
        token = _setup_tenant(client)
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "   "},
        )
        assert resp.status_code in (400, 422)

    def test_html_stripped_and_valid_text_accepted(self, client):
        """HTML tags are stripped; remaining valid text is processed (returns 200)."""
        token = _setup_tenant(client)
        # "<b>What is AI?</b>" → "What is AI?" which is valid
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "<b>What is AI?</b>"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "conversation_id" in data

    def test_xss_attempt_stripped_and_valid_text_accepted(self, client):
        """XSS script tag stripped; remaining text content is used as the question."""
        token = _setup_tenant(client)
        # "<script>xss</script>What is ML?" → "xssWhat is ML?" after strip → valid
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "<script>xss</script>What is ML?"},
        )
        assert resp.status_code == 200

    def test_script_tag_inner_text_used_as_question(self, client):
        """Inner text of a script tag is preserved (tags stripped, text kept)."""
        token = _setup_tenant(client)
        # "<script>evil payload</script>Hello" → "evil payloadHello"
        resp = client.post(
            "/api/v1/chat/",
            headers=auth_header(token),
            json={"question": "<script>evil payload</script>Hello"},
        )
        assert resp.status_code == 200


class TestWebSocketChatSanitization:
    def test_empty_tag_only_message_returns_error(self, client):
        """WebSocket: message with only empty HTML tags becomes empty and is rejected."""
        _, token = register_tenant(client, "ws-san")
        ws_path = f"/api/v1/chat/ws?token={token}"
        with client.websocket_connect(ws_path) as ws:
            ws.send_json({"question": "<b></b>"})
            msg = ws.receive_json()
            assert msg["type"] == "error"
            assert "empty" in msg["content"].lower()

    def test_empty_question_returns_error(self, client):
        """WebSocket: empty question is rejected with an error frame."""
        _, token = register_tenant(client, "ws-empty")
        ws_path = f"/api/v1/chat/ws?token={token}"
        with client.websocket_connect(ws_path) as ws:
            ws.send_json({"question": ""})
            msg = ws.receive_json()
            assert msg["type"] == "error"

    def test_html_stripped_and_question_processed(self, client):
        """WebSocket: HTML tags stripped and remaining text processed normally."""
        _, token = register_tenant(client, "ws-html")
        ws_path = f"/api/v1/chat/ws?token={token}"
        with client.websocket_connect(ws_path) as ws:
            ws.send_json({"question": "<b>Hello</b>"})
            frames = []
            while True:
                msg = ws.receive_json()
                frames.append(msg)
                if msg["type"] in ("done", "error"):
                    break
            # Stripped text "Hello" is valid — should complete normally
            types = [f["type"] for f in frames]
            assert "error" not in types
            assert "done" in types

    def test_whitespace_only_question_returns_error(self, client):
        """WebSocket: whitespace-only question is rejected with an error frame."""
        _, token = register_tenant(client, "ws-ws")
        ws_path = f"/api/v1/chat/ws?token={token}"
        with client.websocket_connect(ws_path) as ws:
            ws.send_json({"question": "   "})
            msg = ws.receive_json()
            assert msg["type"] == "error"
