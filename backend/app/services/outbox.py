import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.event_outbox import EventOutbox


def emit_outbox_event(
    db: Session,
    event_type: str,
    payload: dict,
    event_version: str = "1.0",
) -> EventOutbox:
    """
    Persist an event to the event_outbox table within the caller's active database transaction.
    """
    outbox_entry = EventOutbox(
        id=str(uuid.uuid4()),
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        event_version=event_version,
        payload=payload,
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        retry_count=0,
    )
    db.add(outbox_entry)
    return outbox_entry
