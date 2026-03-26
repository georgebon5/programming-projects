"""
Stripe billing service — manage subscriptions for tenants.

Features:
- Create Stripe customer on registration
- Create checkout sessions for plan upgrades
- Handle webhook events (subscription created/updated/deleted)
- Sync subscription status with tenant.subscription_tier
"""

import logging
from uuid import UUID

import stripe
from sqlalchemy.orm import Session

from app.config import settings
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)

# Map Stripe Price IDs → internal tier names
_PRICE_TO_TIER: dict[str, str] = {}


def _init_stripe() -> None:
    stripe.api_key = settings.stripe_secret_key


def _build_price_map() -> dict[str, str]:
    if not _PRICE_TO_TIER:
        if settings.stripe_price_pro:
            _PRICE_TO_TIER[settings.stripe_price_pro] = "pro"
        if settings.stripe_price_enterprise:
            _PRICE_TO_TIER[settings.stripe_price_enterprise] = "enterprise"
    return _PRICE_TO_TIER


class BillingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        _init_stripe()
        _build_price_map()

    def get_or_create_customer(self, tenant: Tenant) -> str:
        """Ensure tenant has a Stripe customer ID."""
        if tenant.stripe_customer_id:
            return tenant.stripe_customer_id

        customer = stripe.Customer.create(
            name=tenant.name,
            metadata={"tenant_id": str(tenant.id), "slug": tenant.slug},
        )
        tenant.stripe_customer_id = customer.id
        self.db.commit()
        logger.info("Created Stripe customer %s for tenant %s", customer.id, tenant.id)
        return customer.id

    def create_checkout_session(
        self,
        tenant: Tenant,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a Stripe Checkout session and return the URL."""
        customer_id = self.get_or_create_customer(tenant)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"tenant_id": str(tenant.id)},
        )
        return session.url

    def create_portal_session(self, tenant: Tenant, return_url: str) -> str:
        """Create a Stripe Billing Portal session for managing the subscription."""
        customer_id = self.get_or_create_customer(tenant)
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url

    def handle_webhook_event(self, payload: bytes, sig_header: str) -> None:
        """Process a Stripe webhook event."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.stripe_webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            logger.warning("Stripe webhook signature verification failed")
            raise ValueError("Invalid signature")

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            self._on_checkout_completed(data)
        elif event_type in (
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ):
            self._on_subscription_changed(data)
        else:
            logger.debug("Unhandled Stripe event: %s", event_type)

    def _on_checkout_completed(self, session: dict) -> None:
        tenant_id = session.get("metadata", {}).get("tenant_id")
        subscription_id = session.get("subscription")
        if not tenant_id or not subscription_id:
            return

        tenant = self.db.query(Tenant).filter(Tenant.id == UUID(tenant_id)).first()
        if not tenant:
            return

        tenant.stripe_subscription_id = subscription_id
        # Fetch the subscription to determine the tier
        sub = stripe.Subscription.retrieve(subscription_id)
        price_id = sub["items"]["data"][0]["price"]["id"]
        tenant.subscription_tier = _PRICE_TO_TIER.get(price_id, "pro")
        self.db.commit()
        logger.info("Tenant %s upgraded to %s", tenant.id, tenant.subscription_tier)

    def _on_subscription_changed(self, subscription: dict) -> None:
        customer_id = subscription.get("customer")
        if not customer_id:
            return

        tenant = (
            self.db.query(Tenant)
            .filter(Tenant.stripe_customer_id == customer_id)
            .first()
        )
        if not tenant:
            return

        status = subscription.get("status")
        if status in ("canceled", "unpaid", "past_due"):
            tenant.subscription_tier = "free"
            tenant.stripe_subscription_id = None
            logger.info("Tenant %s downgraded to free (status=%s)", tenant.id, status)
        elif status == "active":
            price_id = subscription["items"]["data"][0]["price"]["id"]
            tenant.subscription_tier = _PRICE_TO_TIER.get(price_id, "pro")
            tenant.stripe_subscription_id = subscription["id"]

        self.db.commit()
