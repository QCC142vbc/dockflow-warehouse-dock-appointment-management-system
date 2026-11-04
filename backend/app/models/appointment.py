import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UTCDateTime


class Appointment(Base):
    __tablename__ = "appointments"

    # Unique constraint to help prevent concurrent duplicate bookings
    # For PostgreSQL, this should be enhanced with an exclusion constraint
    # See migration: add_unique_constraint_prevent_concurrent_booking
    __table_args__ = (
        Index(
            'ix_appointments_dock_time_status_unique',
            'dock_id',
            'scheduled_start',
            'scheduled_end',
            'status',
            unique=True,
            postgresql_where="status IN ('PENDING', 'CONFIRMED', 'CHECKED_IN', 'ARRIVED', 'IN_PROGRESS')"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # Stable external UUID identifier for cross-system references (DockFlow Operations)
    appointment_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
        default=lambda: str(uuid.uuid4()),
    )

    reference_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    carrier_id: Mapped[int] = mapped_column(
        ForeignKey("carriers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dock_id: Mapped[int | None] = mapped_column(
        ForeignKey("docks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    scheduled_start: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        index=True,
    )

    scheduled_end: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="PENDING",
        nullable=False,
        index=True,
    )

    vehicle_registration: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    vehicle_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    cargo_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    cargo_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cargo_weight_kg: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    container_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )