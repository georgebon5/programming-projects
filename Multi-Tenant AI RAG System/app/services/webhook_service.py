"""
Service layer for webhook management and event dispatching.
"""

import hashlib
import hmac
import json
import logging
import secrets
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.webhook import WebhookDelivery, WebhookEndpoint

logger = logging.getLogger(__name__)


class WebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_webhook(
        self,
        tenant_id: UUID,
        url: str,
        events: list[str],
        description: str | None = None,
    ) -> WebhookEndpoint:
        """Create a new webhook endpoint with an auto-generated signing secret."""
        secret = secrets.token_urlsafe(32)
        wh = WebhookEndpoint(
            tenant_id=tenant_id,
            url=url,
            secret=secret,
            events=events,
            description=description,
        )
        self.db.add(wh)
        self.db.commit()
        self.db.refresh(wh)
        logger.info("Created webhook %s for tenant %s", wh.id, tenant_id)
        return wh

    def list_webhooks(self, tenant_id: UUID) -> list[WebhookEndpoint]:
        """Return all active webhooks for a tenant."""
        return (
            self.db.query(WebhookEndpoint)
            .filter(
                WebhookEndpoint.tenant_id == tenant_id,
                WebhookEndpoint.is_active.is_(True),
            )
            .all()
        )

    def get_webhook(self, webhook_id: UUID, tenant_id: UUID) -> WebhookEndpoint | None:
        """Fetch a single webhook belonging to a tenant."""
        return (
            self.db.query(WebhookEndpoint)
            .filter(
                WebhookEndpoint.id == webhook_id,
                WebhookEndpoint.tenant_id == tenant_id,
            )
            .first()
        )

    def delete_webhook(self, webhook_id: UUID, tenant_id: UUID) -> bool:
        """Hard-delete a webhook endpoint. Returns True if deleted."""
        wh = self.get_webhook(webhook_id, tenant_id)
        if not wh:
            return False
        self.db.delete(wh)
        self.db.commit()
        logger.info("Deleted webhook %s for tenant %s", webhook_id, tenant_id)
        return True

    def get_deliveries(
        self,
        webhook_id: UUID,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[WebhookDelivery]:
        """Return delivery history for a webhook (tenant-scoped)."""
        if not self.get_webhook(webhook_id, tenant_id):
            return []
        return (
            self.db.query(WebhookDelivery)
            .filter(WebhookDelivery.webhook_id == webhook_id)
            .order_by(WebhookDelivery.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def dispatch_event(self, tenant_id: UUID, event_type: str, payload: dict) -> int:
        """Create delivery records for all active webhooks subscribed to the event.

        Returns the number of delivery records queued.
        """
        webhooks = (
            self.db.query(WebhookEndpoint)
            .filter(
                WebhookEndpoint.tenant_id == tenant_id,
                WebhookEndpoint.is_active.is_(True),
            )
            .all()
        )
        count = 0
        for wh in webhooks:
            if event_type in (wh.events or []):
                delivery = WebhookDelivery(
                    webhook_id=wh.id,
                    event_type=event_type,
                    payload=payload,
                )
                self.db.add(delivery)
                count += 1
        if count:
            self.db.commit()
        logger.debug("Dispatched event %s to %d webhook(s) for tenant %s", event_type, count, tenant_id)
        return count

    @staticmethod
    def sign_payload(secret: str, payload: dict) -> str:
        """Return an HMAC-SHA256 hex digest of the JSON-serialised payload."""
        body = json.dumps(payload, sort_keys=True, default=str)
        return hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
