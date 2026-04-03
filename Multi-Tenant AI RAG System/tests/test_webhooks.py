"""
Tests for the webhook system: CRUD endpoints, dispatch_event, HMAC signing,
admin-only access, and event validation.
"""

import uuid

import pytest

from tests.conftest import auth_header, register_tenant
from app.services.webhook_service import WebhookService

WEBHOOK_URL = "https://example.com/hook"
VALID_EVENTS = ["document.processed", "document.failed"]


# ── Helper ────────────────────────────────────────────────────────────────────

_SENTINEL = object()

def _create_webhook(client, token, url=WEBHOOK_URL, events=_SENTINEL, description=None):
    if events is _SENTINEL:
        events = VALID_EVENTS
    payload = {"url": url, "events": events}
    if description:
        payload["description"] = description
    return client.post("/api/v1/webhooks/", headers=auth_header(token), json=payload)


# ── CRUD: Create ──────────────────────────────────────────────────────────────

class TestCreateWebhook:
    def test_create_webhook_success(self, client):
        _, token = register_tenant(client, f"wh-create-{uuid.uuid4().hex[:6]}")
        resp = _create_webhook(client, token, description="CI hook")
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["url"] == WEBHOOK_URL
        assert set(data["events"]) == set(VALID_EVENTS)
        assert data["is_active"] is True
        assert data["description"] == "CI hook"
        assert "id" in data
        assert "created_at" in data

    def test_create_webhook_invalid_event(self, client):
        _, token = register_tenant(client, f"wh-inv-ev-{uuid.uuid4().hex[:6]}")
        resp = _create_webhook(client, token, events=["document.processed", "bogus.event"])
        assert resp.status_code == 422

    def test_create_webhook_empty_events(self, client):
        _, token = register_tenant(client, f"wh-empty-ev-{uuid.uuid4().hex[:6]}")
        resp = _create_webhook(client, token, events=[])
        assert resp.status_code == 422

    def test_create_webhook_invalid_url(self, client):
        _, token = register_tenant(client, f"wh-bad-url-{uuid.uuid4().hex[:6]}")
        resp = _create_webhook(client, token, url="ftp://invalid.com/hook")
        assert resp.status_code == 422

    def test_create_webhook_member_forbidden(self, client, member_token):
        resp = _create_webhook(client, member_token)
        assert resp.status_code == 403

    def test_create_webhook_unauthenticated(self, client):
        resp = client.post("/api/v1/webhooks/", json={"url": WEBHOOK_URL, "events": VALID_EVENTS})
        assert resp.status_code == 401


# ── CRUD: List ────────────────────────────────────────────────────────────────

class TestListWebhooks:
    def test_list_webhooks_empty(self, client):
        _, token = register_tenant(client, f"wh-list-empty-{uuid.uuid4().hex[:6]}")
        resp = client.get("/api/v1/webhooks/", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["webhooks"] == []

    def test_list_webhooks_multiple(self, client):
        _, token = register_tenant(client, f"wh-list-multi-{uuid.uuid4().hex[:6]}")
        _create_webhook(client, token, url="https://a.example.com/hook")
        _create_webhook(client, token, url="https://b.example.com/hook")
        resp = client.get("/api/v1/webhooks/", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["webhooks"]) == 2

    def test_list_webhooks_tenant_isolation(self, client):
        """Tenant A's webhooks should not appear for tenant B."""
        _, token_a = register_tenant(client, f"wh-iso-a-{uuid.uuid4().hex[:6]}")
        _, token_b = register_tenant(client, f"wh-iso-b-{uuid.uuid4().hex[:6]}")
        _create_webhook(client, token_a)

        resp = client.get("/api/v1/webhooks/", headers=auth_header(token_b))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_member_forbidden(self, client, member_token):
        resp = client.get("/api/v1/webhooks/", headers=auth_header(member_token))
        assert resp.status_code == 403


# ── CRUD: Delete ──────────────────────────────────────────────────────────────

class TestDeleteWebhook:
    def test_delete_webhook_success(self, client):
        _, token = register_tenant(client, f"wh-del-{uuid.uuid4().hex[:6]}")
        create_resp = _create_webhook(client, token)
        wh_id = create_resp.json()["id"]

        del_resp = client.delete(f"/api/v1/webhooks/{wh_id}", headers=auth_header(token))
        assert del_resp.status_code == 204

        # Confirm it's gone
        list_resp = client.get("/api/v1/webhooks/", headers=auth_header(token))
        assert list_resp.json()["total"] == 0

    def test_delete_nonexistent_webhook(self, client):
        _, token = register_tenant(client, f"wh-del-404-{uuid.uuid4().hex[:6]}")
        resp = client.delete(
            f"/api/v1/webhooks/{uuid.uuid4()}",
            headers=auth_header(token),
        )
        assert resp.status_code == 404

    def test_delete_other_tenant_webhook(self, client):
        """Tenant B cannot delete tenant A's webhook."""
        _, token_a = register_tenant(client, f"wh-del-a-{uuid.uuid4().hex[:6]}")
        _, token_b = register_tenant(client, f"wh-del-b-{uuid.uuid4().hex[:6]}")
        wh_id = _create_webhook(client, token_a).json()["id"]

        resp = client.delete(f"/api/v1/webhooks/{wh_id}", headers=auth_header(token_b))
        assert resp.status_code == 404

    def test_delete_member_forbidden(self, client, member_token):
        resp = client.delete(
            f"/api/v1/webhooks/{uuid.uuid4()}",
            headers=auth_header(member_token),
        )
        assert resp.status_code == 403


# ── Deliveries ────────────────────────────────────────────────────────────────

class TestDeliveries:
    def test_deliveries_empty(self, client):
        _, token = register_tenant(client, f"wh-dlv-empty-{uuid.uuid4().hex[:6]}")
        wh_id = _create_webhook(client, token).json()["id"]
        resp = client.get(f"/api/v1/webhooks/{wh_id}/deliveries", headers=auth_header(token))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_deliveries_after_dispatch(self, client, db):
        _, token = register_tenant(client, f"wh-dlv-dispatch-{uuid.uuid4().hex[:6]}")
        wh_data = _create_webhook(client, token, events=["document.processed"]).json()
        wh_id = wh_data["id"]

        # Manually dispatch using the service
        from app.models.webhook import WebhookEndpoint
        wh_obj = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == uuid.UUID(wh_id)).first()
        svc = WebhookService(db)
        count = svc.dispatch_event(
            tenant_id=wh_obj.tenant_id,
            event_type="document.processed",
            payload={"document_id": "abc123"},
        )
        assert count == 1

        resp = client.get(f"/api/v1/webhooks/{wh_id}/deliveries", headers=auth_header(token))
        assert resp.status_code == 200
        deliveries = resp.json()
        assert len(deliveries) == 1
        assert deliveries[0]["event_type"] == "document.processed"
        assert deliveries[0]["attempt_count"] == 0

    def test_deliveries_wrong_tenant(self, client):
        _, token_a = register_tenant(client, f"wh-dlv-a-{uuid.uuid4().hex[:6]}")
        _, token_b = register_tenant(client, f"wh-dlv-b-{uuid.uuid4().hex[:6]}")
        wh_id = _create_webhook(client, token_a).json()["id"]

        resp = client.get(f"/api/v1/webhooks/{wh_id}/deliveries", headers=auth_header(token_b))
        assert resp.status_code == 404


# ── dispatch_event (service layer) ───────────────────────────────────────────

class TestDispatchEvent:
    def test_dispatch_only_matching_events(self, client, db):
        """Only webhooks subscribed to the event should get a delivery record."""
        _, token = register_tenant(client, f"wh-disp-match-{uuid.uuid4().hex[:6]}")
        _create_webhook(client, token, events=["document.processed"])
        _create_webhook(client, token, url="https://b.example.com/hook", events=["document.failed"])

        from app.models.webhook import WebhookEndpoint
        # Get tenant_id from one of the webhooks
        wh = db.query(WebhookEndpoint).filter(WebhookEndpoint.is_active.is_(True)).first()
        svc = WebhookService(db)
        count = svc.dispatch_event(
            tenant_id=wh.tenant_id,
            event_type="document.processed",
            payload={"id": "x"},
        )
        assert count == 1

    def test_dispatch_no_subscribers(self, client, db):
        _, token = register_tenant(client, f"wh-disp-none-{uuid.uuid4().hex[:6]}")
        _create_webhook(client, token, events=["document.processed"])

        from app.models.webhook import WebhookEndpoint
        wh = db.query(WebhookEndpoint).filter(WebhookEndpoint.is_active.is_(True)).first()
        svc = WebhookService(db)
        count = svc.dispatch_event(
            tenant_id=wh.tenant_id,
            event_type="user.deleted",
            payload={},
        )
        assert count == 0

    def test_dispatch_multiple_matching_webhooks(self, client, db):
        _, token = register_tenant(client, f"wh-disp-multi-{uuid.uuid4().hex[:6]}")
        _create_webhook(client, token, url="https://a.example.com/hook", events=["document.uploaded"])
        _create_webhook(client, token, url="https://b.example.com/hook", events=["document.uploaded"])
        _create_webhook(client, token, url="https://c.example.com/hook", events=["document.failed"])

        from app.models.webhook import WebhookEndpoint
        wh = db.query(WebhookEndpoint).filter(WebhookEndpoint.is_active.is_(True)).first()
        svc = WebhookService(db)
        count = svc.dispatch_event(
            tenant_id=wh.tenant_id,
            event_type="document.uploaded",
            payload={"doc": "y"},
        )
        assert count == 2


# ── HMAC signing ─────────────────────────────────────────────────────────────

class TestHMACSigning:
    def test_sign_payload_deterministic(self):
        secret = "supersecret"
        payload = {"event": "document.processed", "id": "abc"}
        sig1 = WebhookService.sign_payload(secret, payload)
        sig2 = WebhookService.sign_payload(secret, payload)
        assert sig1 == sig2

    def test_sign_payload_different_secrets(self):
        payload = {"event": "document.processed", "id": "abc"}
        sig1 = WebhookService.sign_payload("secret-a", payload)
        sig2 = WebhookService.sign_payload("secret-b", payload)
        assert sig1 != sig2

    def test_sign_payload_different_payloads(self):
        secret = "same-secret"
        sig1 = WebhookService.sign_payload(secret, {"event": "a"})
        sig2 = WebhookService.sign_payload(secret, {"event": "b"})
        assert sig1 != sig2

    def test_sign_payload_returns_hex_string(self):
        sig = WebhookService.sign_payload("secret", {"x": 1})
        assert isinstance(sig, str)
        # SHA-256 hex digest is 64 chars
        assert len(sig) == 64
        int(sig, 16)  # must be valid hex

    def test_sign_payload_key_order_invariant(self):
        """JSON is sorted by key, so key order in the dict must not matter."""
        secret = "s"
        sig1 = WebhookService.sign_payload(secret, {"a": 1, "b": 2})
        sig2 = WebhookService.sign_payload(secret, {"b": 2, "a": 1})
        assert sig1 == sig2


# ── Test endpoint ─────────────────────────────────────────────────────────────

class TestWebhookTest:
    def test_test_endpoint_returns_signature(self, client):
        _, token = register_tenant(client, f"wh-test-ep-{uuid.uuid4().hex[:6]}")
        wh_id = _create_webhook(client, token).json()["id"]
        resp = client.post(f"/api/v1/webhooks/{wh_id}/test", headers=auth_header(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["queued"] is True
        assert data["event"] == "webhook.test"
        assert "signature" in data
        assert len(data["signature"]) == 64

    def test_test_endpoint_nonexistent_webhook(self, client):
        _, token = register_tenant(client, f"wh-test-404-{uuid.uuid4().hex[:6]}")
        resp = client.post(f"/api/v1/webhooks/{uuid.uuid4()}/test", headers=auth_header(token))
        assert resp.status_code == 404

    def test_test_endpoint_member_forbidden(self, client, member_token):
        resp = client.post(f"/api/v1/webhooks/{uuid.uuid4()}/test", headers=auth_header(member_token))
        assert resp.status_code == 403
