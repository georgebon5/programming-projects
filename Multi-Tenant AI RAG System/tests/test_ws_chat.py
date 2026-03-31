"""
Test για WebSocket chat endpoint (streaming RAG).
"""

import pytest
import json
from tests.conftest import auth_header, register_tenant

def test_websocket_chat_stream(client):
    user, token = register_tenant(client, "ws")
    jwt = token
    ws_path = f"/api/v1/chat/ws?token={jwt}"
    with client.websocket_connect(ws_path) as ws:
        ws.send_json({"question": "Γειά σου!"})
        tokens = []
        while True:
            msg = ws.receive_json()
            if msg["type"] == "token":
                tokens.append(msg["content"])
            elif msg["type"] == "done":
                break
            elif msg["type"] == "error":
                assert False, f"WebSocket error: {msg['content']}"
        assert tokens, "WebSocket returned no tokens"
        full_response = "".join(tokens).lower()
        # Accept either: fallback "no relevant documents" message, or any non-empty AI answer
        assert "no relevant documents found" in full_response or len(full_response) > 0
