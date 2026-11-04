"""add unique constraint prevent concurrent booking

Revision ID: add_unique_constraint_prevent_concurrent_booking
Revises: c2da3cce73bb
Create Date: 2026-10-31 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'add_unique_constraint_prevent_concurrent_booking'
down_revision: Union[str, Sequence[str], None] = 'c2da3cce73bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add a unique constraint to prevent concurrent bookings on the same dock
    # at the same time with the same status. This is a partial fix for the race condition.
    # For PostgreSQL, this should be enhanced with an exclusion constraint in production.
    
    # SQLite compatible approach: unique constraint on (dock_id, scheduled_start, scheduled_end, status)
    # This prevents exact duplicate bookings but not overlapping time ranges
    op.create_index(
        'ix_appointments_dock_time_status_unique',
        'appointments',
        ['dock_id', 'scheduled_start', 'scheduled_end', 'status'],
        unique=True,
        postgresql_where=text("status IN ('PENDING', 'CONFIRMED', 'CHECKED_IN', 'ARRIVED', 'IN_PROGRESS')")
    )
    
    # For PostgreSQL, we should add an exclusion constraint to prevent overlapping appointments
    # This is commented out for SQLite compatibility, but should be enabled in production
    # op.execute("""
    #     ALTER TABLE appointments
    #     ADD CONSTRAINT prevent_appointment_overlap
    #     EXCLUDE USING GIST (
    #         dock_id WITH =,
    #         tsrange(scheduled_start, scheduled_end) WITH &&
    #     )
    #     WHERE (status IN ('PENDING', 'CONFIRMED', 'CHECKED_IN', 'ARRIVED', 'IN_PROGRESS'))
    # """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_appointments_dock_time_status_unique', table_name='appointments')
    
    # For PostgreSQL, drop the exclusion constraint
    # op.execute("""
    #     ALTER TABLE appointments
    #     DROP CONSTRAINT IF EXISTS prevent_appointment_overlap
    # """)
