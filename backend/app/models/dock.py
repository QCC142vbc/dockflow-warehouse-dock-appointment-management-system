from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UTCDateTime


class Dock(Base):
    __tablename__ = "docks"

    __table_args__ = (
        UniqueConstraint(
            "dock_code",
            "warehouse_id",
            name="uq_dock_code_warehouse",
        ),
        UniqueConstraint(
            "external_dock_id",
            name="uq_external_dock_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    # External UUID for cross-system references (DockFlow Operations)
    external_dock_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        unique=True,
        index=True,
    )

    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dock_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    max_vehicle_length: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    max_vehicle_weight: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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