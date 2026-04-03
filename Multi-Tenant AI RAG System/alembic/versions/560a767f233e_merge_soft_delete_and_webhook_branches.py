"""merge soft_delete and webhook branches

Revision ID: 560a767f233e
Revises: 727927e18a22, c3f1a8b209e0
Create Date: 2026-04-03 22:47:02.142364

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '560a767f233e'
down_revision: Union[str, None] = ('727927e18a22', 'c3f1a8b209e0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
