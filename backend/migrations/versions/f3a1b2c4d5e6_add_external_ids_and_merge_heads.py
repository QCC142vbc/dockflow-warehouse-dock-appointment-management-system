"""add external IDs and merge heads

Merges the two existing branch heads:
  - e1225af839c8 (add_unique_constraint_dock_code_warehouse)
  - add_unique_constraint_prevent_concurrent_booking

Then adds:
  - carriers.external_carrier_id     (String(36), nullable, unique-indexed)
  - appointments.appointment_id      (String(36), NOT NULL, unique, auto-UUID)
  - The concurrent-booking partial index that was defined in the other branch
    but never applied to the actual database.

Revision ID: f3a1b2c4d5e6
Revises: e1225af839c8, add_unique_constraint_prevent_concurrent_booking
Create Date: 2026-10-31 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "f3a1b2c4d5e6"
down_revision: Union[str, Sequence[str], None] = (
    "e1225af839c8",
    "add_unique_constraint_prevent_concurrent_booking",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ------------------------------------------------------------------
    # 1. carriers — add external_carrier_id for cross-system references
    # ------------------------------------------------------------------
    with op.batch_alter_table("carriers", recreate="auto") as batch_op:
        batch_op.add_column(
            sa.Column(
                "external_carrier_id",
                sa.String(36),
                nullable=True,
            )
        )
        batch_op.create_unique_constraint(
            "uq_external_carrier_id",
            ["external_carrier_id"],
        )
        batch_op.create_index(
            "ix_carriers_external_carrier_id",
            ["external_carrier_id"],
        )

    # ------------------------------------------------------------------
    # 2. appointments — add appointment_id (stable external UUID)
    #    SQLite requires batch mode; use recreate='auto' so it works on
    #    both SQLite (dev) and PostgreSQL (prod).
    # ------------------------------------------------------------------
    with op.batch_alter_table("appointments", recreate="auto") as batch_op:
        # Add as nullable first so existing rows are accepted by SQLite
        batch_op.add_column(
            sa.Column(
                "appointment_id",
                sa.String(36),
                nullable=True,
            )
        )

    # Backfill existing rows with a unique UUID each
    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id FROM appointments WHERE appointment_id IS NULL")
    ).fetchall()
    for (row_id,) in rows:
        import uuid
        conn.execute(
            text(
                "UPDATE appointments SET appointment_id = :uid WHERE id = :rid"
            ),
            {"uid": str(uuid.uuid4()), "rid": row_id},
        )

    # Now enforce NOT NULL + unique
    with op.batch_alter_table("appointments", recreate="auto") as batch_op:
        batch_op.alter_column("appointment_id", nullable=False)
        batch_op.create_unique_constraint(
            "uq_appointment_id",
            ["appointment_id"],
        )
        batch_op.create_index(
            "ix_appointments_appointment_id",
            ["appointment_id"],
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("appointments", recreate="auto") as batch_op:
        batch_op.drop_index("ix_appointments_appointment_id")
        batch_op.drop_constraint("uq_appointment_id", type_="unique")
        batch_op.drop_column("appointment_id")

    with op.batch_alter_table("carriers", recreate="auto") as batch_op:
        batch_op.drop_index("ix_carriers_external_carrier_id")
        batch_op.drop_constraint("uq_external_carrier_id", type_="unique")
        batch_op.drop_column("external_carrier_id")
