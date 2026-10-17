from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, UTCDateTime


class DockUnavailability(Base):
    __tablename__ = "dock_unavailability"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    dock_id: Mapped[int] = mapped_column(
        ForeignKey("docks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reason_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    start_time: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        index=True,
    )

    end_time: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
    )

    reported_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )