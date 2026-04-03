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
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("totp_secret", sa.String(64), nullable=True))
        batch_op.add_column(sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default="false"))

    # ── Tenant: Stripe billing fields ──
    with op.batch_alter_table("tenants", schema=None) as batch_op:
        batch_op.add_column(sa.Column("stripe_customer_id", sa.String(255), nullable=True))
        batch_op.add_column(sa.Column("stripe_subscription_id", sa.String(255), nullable=True))
        batch_op.create_unique_constraint("uq_tenants_stripe_customer_id", ["stripe_customer_id"])
        batch_op.create_unique_constraint("uq_tenants_stripe_subscription_id", ["stripe_subscription_id"])


def downgrade() -> None:
    # Dropping the columns automatically removes any constraints on them in
    # batch mode (SQLite copy-and-move strategy reconstructs the table without
    # the columns and their associated unique constraints).
    with op.batch_alter_table("tenants", schema=None) as batch_op:
        batch_op.drop_column("stripe_subscription_id")
        batch_op.drop_column("stripe_customer_id")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("totp_enabled")
        batch_op.drop_column("totp_secret")
