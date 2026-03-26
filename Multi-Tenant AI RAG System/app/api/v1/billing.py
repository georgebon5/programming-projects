"""Billing endpoints — Stripe checkout, portal, and webhooks."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from app.config import settings
from app.db.database import get_db
from app.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.services.billing_service import BillingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


def _require_stripe() -> None:
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Billing is not configured",
        )


class CheckoutRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class PortalRequest(BaseModel):
    return_url: str


@router.post("/checkout")
def create_checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> dict:
    """Create a Stripe Checkout session for the tenant."""
    _require_stripe()
    svc = BillingService(db)
    url = svc.create_checkout_session(
        tenant=current_user.tenant,
        price_id=payload.price_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
    )
    return {"checkout_url": url}


@router.post("/portal")
def create_portal(
    payload: PortalRequest,
    current_user: User = Depends(require_role({UserRole.ADMIN})),
    db: Session = Depends(get_db),
) -> dict:
    """Create a Stripe Billing Portal session to manage the subscription."""
    _require_stripe()
    svc = BillingService(db)
    url = svc.create_portal_session(
        tenant=current_user.tenant,
        return_url=payload.return_url,
    )
    return {"portal_url": url}


@router.get("/status")
def billing_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get the current billing status for the tenant."""
    tenant = current_user.tenant
    return {
        "subscription_tier": tenant.subscription_tier,
        "stripe_customer_id": tenant.stripe_customer_id,
        "stripe_subscription_id": tenant.stripe_subscription_id,
    }


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    """Handle Stripe webhook events. Must be called by Stripe servers only."""
    _require_stripe()
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    svc = BillingService(db)
    try:
        svc.handle_webhook_event(payload, sig)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"status": "ok"}
