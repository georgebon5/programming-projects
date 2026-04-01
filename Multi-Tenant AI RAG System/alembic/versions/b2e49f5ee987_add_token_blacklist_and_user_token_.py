"""Add token blacklist and user token revocation

Revision ID: b2e49f5ee987
Revises: a8f3c2d901b5
Create Date: 2026-04-01 22:19:13.216994

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e49f5ee987'
down_revision: Union[str, None] = 'a8f3c2d901b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    from alembic import op as _op

    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    # Create blacklisted_tokens table (idempotent: skip if already exists)
    if 'blacklisted_tokens' not in existing_tables:
        op.create_table(
            'blacklisted_tokens',
            sa.Column('id', sa.Uuid(), nullable=False),
            sa.Column('jti', sa.String(length=64), nullable=False),
            sa.Column('token_type', sa.String(length=16), nullable=False),
            sa.Column('user_id', sa.Uuid(), nullable=False),
            sa.Column('tenant_id', sa.Uuid(), nullable=False),
            sa.Column('blacklisted_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('jti'),
        )
        op.create_index('ix_blacklisted_tokens_jti', 'blacklisted_tokens', ['jti'], unique=True)
        op.create_index('ix_blacklisted_tokens_user_id', 'blacklisted_tokens', ['user_id'], unique=False)
        op.create_index('ix_blacklisted_tokens_tenant_id', 'blacklisted_tokens', ['tenant_id'], unique=False)
        op.create_index('ix_blacklisted_tokens_expires_at', 'blacklisted_tokens', ['expires_at'], unique=False)

    # Add tokens_revoked_at to users (idempotent: skip if column already exists)
    user_columns = [col['name'] for col in inspector.get_columns('users')]
    if 'tokens_revoked_at' not in user_columns:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('tokens_revoked_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('tokens_revoked_at')

    op.drop_index('ix_blacklisted_tokens_expires_at', table_name='blacklisted_tokens')
    op.drop_index('ix_blacklisted_tokens_tenant_id', table_name='blacklisted_tokens')
    op.drop_index('ix_blacklisted_tokens_user_id', table_name='blacklisted_tokens')
    op.drop_index('ix_blacklisted_tokens_jti', table_name='blacklisted_tokens')
    op.drop_table('blacklisted_tokens')
