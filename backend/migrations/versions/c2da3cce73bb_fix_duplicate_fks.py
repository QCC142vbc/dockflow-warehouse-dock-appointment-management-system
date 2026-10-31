"""fix_duplicate_fks

Revision ID: c2da3cce73bb
Revises: 1081e647ec46
Create Date: 2026-10-18 15:15:26.890305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2da3cce73bb'
down_revision: Union[str, Sequence[str], None] = '1081e647ec46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Recreate appointments table to remove duplicate foreign keys
    # SQLite batch mode will recreate the table with only the CASCADE FKs
    with op.batch_alter_table('appointments', recreate='auto') as batch_op:
        # Columns
        batch_op.alter_column('id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('reference_number', existing_type=sa.String(length=50), nullable=False)
        batch_op.alter_column('carrier_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('warehouse_id', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('dock_id', existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column('created_by', existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column('scheduled_start', existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column('scheduled_end', existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column('status', existing_type=sa.String(length=30), nullable=False)
        batch_op.alter_column('vehicle_registration', existing_type=sa.String(length=30), nullable=False)
        batch_op.alter_column('vehicle_type', existing_type=sa.String(length=50), nullable=False)
        batch_op.alter_column('cargo_type', existing_type=sa.String(length=100), nullable=False)
        batch_op.alter_column('cargo_description', existing_type=sa.Text(), nullable=True)
        batch_op.alter_column('cargo_weight_kg', existing_type=sa.Float(), nullable=True)
        batch_op.alter_column('container_number', existing_type=sa.String(length=30), nullable=True)
        batch_op.alter_column('notes', existing_type=sa.Text(), nullable=True)
        batch_op.alter_column('rejection_reason', existing_type=sa.Text(), nullable=True)
        batch_op.alter_column('created_at', existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column('updated_at', existing_type=sa.DateTime(timezone=True), nullable=False)

        # Foreign keys with CASCADE
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
        # Recreate without CASCADE
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
