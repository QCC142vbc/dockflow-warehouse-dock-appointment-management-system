"""add_unique_constraint_dock_code_warehouse

Revision ID: e1225af839c8
Revises: c2da3cce73bb
Create Date: 2026-10-18 15:18:39.278557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1225af839c8'
down_revision: Union[str, Sequence[str], None] = 'c2da3cce73bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraint on dock_code + warehouse_id
    with op.batch_alter_table('docks', recreate='auto') as batch_op:
        batch_op.create_unique_constraint(
            'uq_dock_code_warehouse',
            ['dock_code', 'warehouse_id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('docks', recreate='auto') as batch_op:
        batch_op.drop_constraint('uq_dock_code_warehouse', type_='unique')
