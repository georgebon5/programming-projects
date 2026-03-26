"""Add 2FA and Stripe billing fields

Revision ID: a8f3c2d901b5
Revises: 14774df175ad
Create Date: 2025-01-15 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "a8f3c2d901b5"
down_revision: Union[str, None] = "14774df175ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── User: 2FA fields ──
    op.add_column("users", sa.Column("totp_secret", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default="false"))

    # ── Tenant: Stripe billing fields ──
    op.add_column("tenants", sa.Column("stripe_customer_id", sa.String(255), nullable=True))
    op.add_column("tenants", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_tenants_stripe_customer_id", "tenants", ["stripe_customer_id"])
    op.create_unique_constraint("uq_tenants_stripe_subscription_id", "tenants", ["stripe_subscription_id"])


def downgrade() -> None:
    op.drop_constraint("uq_tenants_stripe_subscription_id", "tenants", type_="unique")
    op.drop_constraint("uq_tenants_stripe_customer_id", "tenants", type_="unique")
    op.drop_column("tenants", "stripe_subscription_id")
    op.drop_column("tenants", "stripe_customer_id")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret")
