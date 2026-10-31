"""add_fk_cascades_to_appointments

Revision ID: 1081e647ec46
Revises: 497955b21c00
Create Date: 2026-10-18 15:12:11.274916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1081e647ec46'
down_revision: Union[str, Sequence[str], None] = '497955b21c00'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite doesn't support ALTER CONSTRAINT directly
    # Use batch mode to recreate the table with ON DELETE CASCADE
    with op.batch_alter_table('appointments', recreate='auto') as batch_op:
        batch_op.create_foreign_key(
            'fk_appointments_carrier_id_carriers',
            'carriers',
            ['carrier_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'fk_appointments_warehouse_id_warehouses',
            'warehouses',
            ['warehouse_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'fk_appointments_dock_id_docks',
            'docks',
            ['dock_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.create_foreign_key(
            'fk_appointments_created_by_users',
            'users',
            ['created_by'],
            ['id'],
            ondelete='CASCADE'
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('appointments', recreate='auto') as batch_op:
        batch_op.create_foreign_key(
            'fk_appointments_carrier_id_carriers',
            'carriers',
            ['carrier_id'],
            ['id']
        )
        batch_op.create_foreign_key(
            'fk_appointments_warehouse_id_warehouses',
            'warehouses',
            ['warehouse_id'],
            ['id']
        )
        batch_op.create_foreign_key(
            'fk_appointments_dock_id_docks',
            'docks',
            ['dock_id'],
            ['id']
        )
        batch_op.create_foreign_key(
            'fk_appointments_created_by_users',
            'users',
            ['created_by'],
            ['id']
        )
