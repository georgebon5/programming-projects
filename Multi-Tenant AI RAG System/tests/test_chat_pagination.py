"""
Tests for chat conversation list pagination.

Covers:
- Default skip/limit values
- skip and limit params
- X-Total-Count header
- Page boundary behaviour
- Independent tenant isolation
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header, register_tenant


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _send_messages(client: TestClient, token: str, n: int) -> list[str]:
    """Create *n* distinct conversations and return their IDs."""
    ids: list[str] = []
    for i in range(n):
        resp = client.post(
            "/api/v1/chat/",
            json={"question": f"Question number {i}", "n_context_chunks": 1},
            headers=auth_header(token),
        )
        assert resp.status_code == 200, resp.text
        ids.append(resp.json()["conversation_id"])
    return ids


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tenant(client):
    """Register a tenant and return (client, token)."""
    _, token = register_tenant(client)
    return client, token


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestListConversationsDefault:
    """Verify the endpoint works with no pagination params."""

    def test_empty_returns_zero(self, tenant):
        client, token = tenant
        resp = client.get("/api/v1/chat/", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["conversations"] == []

    def test_default_limit_is_20(self, tenant):
        """Create 25 conversations; default response should return 20."""
        client, token = tenant
        _send_messages(client, token, 25)

        resp = client.get("/api/v1/chat/", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 25
        assert len(body["conversations"]) == 20

    def test_x_total_count_header_present(self, tenant):
        client, token = tenant
        _send_messages(client, token, 3)

        resp = client.get("/api/v1/chat/", headers=auth_header(token))
        assert resp.status_code == 200
        assert "x-total-count" in resp.headers
        assert resp.headers["x-total-count"] == "3"


class TestListConversationsLimit:
    """Verify the ``limit`` query parameter."""

    def test_limit_respected(self, tenant):
        client, token = tenant
        _send_messages(client, token, 10)

        resp = client.get("/api/v1/chat/?limit=5", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["conversations"]) == 5
        assert body["total"] == 10

    def test_limit_larger_than_total(self, tenant):
        client, token = tenant
        _send_messages(client, token, 3)

        resp = client.get("/api/v1/chat/?limit=50", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["conversations"]) == 3
        assert body["total"] == 3

    def test_limit_zero_rejected(self, tenant):
        client, token = tenant
        resp = client.get("/api/v1/chat/?limit=0", headers=auth_header(token))
        assert resp.status_code == 422

    def test_limit_over_100_rejected(self, tenant):
        client, token = tenant
        resp = client.get("/api/v1/chat/?limit=101", headers=auth_header(token))
        assert resp.status_code == 422


class TestListConversationsSkip:
    """Verify the ``skip`` query parameter."""

    def test_skip_offsets_results(self, tenant):
        client, token = tenant
        # 5 conversations; each page of 3 should be distinct
        _send_messages(client, token, 5)

        page1 = client.get("/api/v1/chat/?skip=0&limit=3", headers=auth_header(token))
        page2 = client.get("/api/v1/chat/?skip=3&limit=3", headers=auth_header(token))
        assert page1.status_code == 200
        assert page2.status_code == 200

        ids1 = {c["conversation_id"] for c in page1.json()["conversations"]}
        ids2 = {c["conversation_id"] for c in page2.json()["conversations"]}
        # No overlap
        assert ids1.isdisjoint(ids2)
        # Together they cover all 5
        assert len(ids1 | ids2) == 5

    def test_skip_beyond_total_returns_empty(self, tenant):
        client, token = tenant
        _send_messages(client, token, 3)

        resp = client.get("/api/v1/chat/?skip=100", headers=auth_header(token))
        assert resp.status_code == 200
        body = resp.json()
        assert body["conversations"] == []
        assert body["total"] == 3  # total is still accurate

    def test_skip_negative_rejected(self, tenant):
        client, token = tenant
        resp = client.get("/api/v1/chat/?skip=-1", headers=auth_header(token))
        assert resp.status_code == 422

    def test_x_total_count_consistent_across_pages(self, tenant):
        """X-Total-Count must be the same regardless of which page is requested."""
        client, token = tenant
        _send_messages(client, token, 7)

        for skip in (0, 3, 6, 10):
            resp = client.get(f"/api/v1/chat/?skip={skip}&limit=3", headers=auth_header(token))
            assert resp.status_code == 200
            assert resp.headers["x-total-count"] == "7", f"failed for skip={skip}"


class TestListConversationsTenantIsolation:
    """Conversations from another tenant must not appear."""

    def test_tenants_see_only_own_conversations(self, client):
        _, token_a = register_tenant(client)
        _, token_b = register_tenant(client)

        _send_messages(client, token_a, 4)
        _send_messages(client, token_b, 2)

        resp_a = client.get("/api/v1/chat/", headers=auth_header(token_a))
        resp_b = client.get("/api/v1/chat/", headers=auth_header(token_b))

        assert resp_a.json()["total"] == 4
        assert resp_b.json()["total"] == 2
        assert resp_a.headers["x-total-count"] == "4"
        assert resp_b.headers["x-total-count"] == "2"


class TestListConversationsResponseShape:
    """Verify the response payload structure."""

    def test_conversation_summary_fields(self, tenant):
        client, token = tenant
        _send_messages(client, token, 1)

        resp = client.get("/api/v1/chat/", headers=auth_header(token))
        assert resp.status_code == 200
        conv = resp.json()["conversations"][0]
        assert "conversation_id" in conv
        assert "message_count" in conv
        assert "started_at" in conv
        assert "last_message_at" in conv
        assert "preview" in conv
        assert conv["message_count"] >= 1
