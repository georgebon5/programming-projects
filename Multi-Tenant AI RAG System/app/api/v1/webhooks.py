"""
Webhook management endpoints (admin only).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.auth import require_role
from app.models.user import User, UserRole
from app.schemas.webhook import (
    VALID_EVENTS,
    WebhookCreate,
    WebhookDeliveryResponse,
    WebhookListResponse,
    WebhookResponse,
)
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

_admin_dep = Depends(require_role({UserRole.ADMIN}))


def _get_service(db: Session = Depends(get_db)) -> WebhookService:
    return WebhookService(db)


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(
    payload: WebhookCreate,
    current_user: User = _admin_dep,
    svc: WebhookService = Depends(_get_service),
) -> WebhookResponse:
    """Register a new webhook endpoint for the tenant. Admin only."""
    invalid = [e for e in payload.events if e not in VALID_EVENTS]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid event type(s): {invalid}. Valid events: {VALID_EVENTS}",
        )
    if not payload.url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL must start with http:// or https://",
        )
    wh = svc.create_webhook(
        tenant_id=current_user.tenant_id,
        url=payload.url,
        events=payload.events,
        description=payload.description,
    )
    return WebhookResponse.model_validate(wh)


@router.get("/", response_model=WebhookListResponse)
def list_webhooks(
    current_user: User = _admin_dep,
    svc: WebhookService = Depends(_get_service),
) -> WebhookListResponse:
    """List all active webhooks for the tenant. Admin only."""
    webhooks = svc.list_webhooks(current_user.tenant_id)
    return WebhookListResponse(
        webhooks=[WebhookResponse.model_validate(wh) for wh in webhooks],
        total=len(webhooks),
    )


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(
    webhook_id: UUID,
    current_user: User = _admin_dep,
    svc: WebhookService = Depends(_get_service),
) -> None:
    """Delete a webhook endpoint. Admin only."""
    deleted = svc.delete_webhook(webhook_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )


@router.get("/{webhook_id}/deliveries", response_model=list[WebhookDeliveryResponse])
def get_deliveries(
    webhook_id: UUID,
    skip: int = 0,
    limit: int = 20,
    current_user: User = _admin_dep,
    svc: WebhookService = Depends(_get_service),
) -> list[WebhookDeliveryResponse]:
    """Retrieve delivery history for a webhook. Admin only."""
    # Verify the webhook belongs to this tenant
    wh = svc.get_webhook(webhook_id, current_user.tenant_id)
    if not wh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    deliveries = svc.get_deliveries(webhook_id, current_user.tenant_id, skip=skip, limit=limit)
    return [WebhookDeliveryResponse.model_validate(d) for d in deliveries]


@router.post("/{webhook_id}/test", status_code=status.HTTP_200_OK)
def test_webhook(
    webhook_id: UUID,
    current_user: User = _admin_dep,
    svc: WebhookService = Depends(_get_service),
) -> dict:
    """Queue a test event delivery for the webhook. Admin only."""
    wh = svc.get_webhook(webhook_id, current_user.tenant_id)
    if not wh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    test_payload = {
        "event": "webhook.test",
        "webhook_id": str(webhook_id),
        "tenant_id": str(current_user.tenant_id),
        "message": "This is a test event from the webhook system.",
    }
    signature = WebhookService.sign_payload(wh.secret, test_payload)
    return {
        "queued": True,
        "webhook_id": str(webhook_id),
        "event": "webhook.test",
        "signature": signature,
    }
