from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UTCDateTime


class DockCapability(Base):
    __tablename__ = "dock_capabilities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    dock_id: Mapped[int] = mapped_column(
        ForeignKey("docks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    capability_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    capability_value: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(300),
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