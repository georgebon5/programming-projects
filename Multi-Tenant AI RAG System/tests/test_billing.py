"""
Tests για Stripe Billing endpoints: checkout, portal, status (mocked Stripe).
"""


import pytest
import os
from unittest.mock import MagicMock, patch
from tests.conftest import auth_header, register_tenant


# Fixture για mock Stripe secret key
@pytest.fixture(autouse=True)
def set_stripe_key(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_123")
    # Επίσης κάνε reload τα settings αν χρειάζεται
    from app.config import settings as app_settings
    app_settings.stripe_secret_key = "sk_test_123"

class TestBilling:
    @patch("app.services.billing_service.stripe")
    def test_checkout_and_portal(self, mock_stripe, client):
        # Mock Stripe responses with proper MagicMock instances
        mock_customer = MagicMock()
        mock_customer.id = "cus_test"
        mock_stripe.Customer.create.return_value = mock_customer

        mock_checkout = MagicMock()
        mock_checkout.url = "https://stripe.test/checkout"
        mock_stripe.checkout.Session.create.return_value = mock_checkout

        mock_portal = MagicMock()
        mock_portal.url = "https://stripe.test/portal"
        mock_stripe.billing_portal.Session.create.return_value = mock_portal

        user, token = register_tenant(client, "billing")
        headers = auth_header(token)

        # Checkout
        resp = client.post(
            "/api/v1/billing/checkout",
            json={
                "price_id": "price_test",
                "success_url": "https://success.local",
                "cancel_url": "https://cancel.local",
            },
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["checkout_url"].startswith("https://stripe.test/checkout")

        # Portal
        resp2 = client.post(
            "/api/v1/billing/portal",
            json={"return_url": "https://return.local"},
            headers=headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["portal_url"].startswith("https://stripe.test/portal")

        # Status
        resp3 = client.get("/api/v1/billing/status", headers=headers)
        assert resp3.status_code == 200
        assert "subscription_tier" in resp3.json()
