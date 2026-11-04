import os
import sys
import time
import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import create_service_access_token
from app.models.event_outbox import EventOutbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("outbox_worker")

OPERATIONS_API_BASE = os.getenv("OPERATIONS_API_URL", "http://localhost:8001/api/v1/integration")
DISPATCH_BATCH_SIZE = int(os.getenv("OUTBOX_BATCH_SIZE", "20"))
POLL_INTERVAL_SECONDS = float(os.getenv("OUTBOX_POLL_INTERVAL", "2.0"))


def dispatch_event(client: httpx.Client, event: EventOutbox) -> bool:
    """Send an outbox event to the corresponding Operations integration endpoint."""
    payload = event.payload
    event_type = event.event_type

    url_map = {
        "appointment.created": f"{OPERATIONS_API_BASE}/sync/appointment",
        "appointment.updated": f"{OPERATIONS_API_BASE}/sync/appointment",
        "warehouse.created": f"{OPERATIONS_API_BASE}/sync/warehouse",
        "warehouse.updated": f"{OPERATIONS_API_BASE}/sync/warehouse",
        "dock.created": f"{OPERATIONS_API_BASE}/sync/dock",
        "dock.updated": f"{OPERATIONS_API_BASE}/sync/dock",
        "carrier.created": f"{OPERATIONS_API_BASE}/sync/carrier",
        "carrier.updated": f"{OPERATIONS_API_BASE}/sync/carrier",
    }

    target_url = url_map.get(event_type)
    if not target_url:
        logger.warning(f"No integration route for event_type '{event_type}', marking as ignored.")
        return True

    authorization = f"Bearer {create_service_access_token()}"
    try:
        response = client.post(
            target_url,
            json=payload,
            headers={"Authorization": authorization},
            timeout=5.0,
        )
        if response.status_code in (200, 201, 202):
            logger.info(f"Successfully synced event {event.event_id} ({event_type}) -> {target_url}")
            return True
        else:
            logger.error(
                f"Failed to sync event {event.event_id}: HTTP {response.status_code} - {response.text}"
            )
            return False
    except Exception as exc:
        logger.error(f"Network error syncing event {event.event_id} to {target_url}: {exc}")
        return False


def process_pending_outbox_events(db: Session, client: httpx.Client) -> int:
    """Fetch pending outbox events and dispatch them."""
    statement = (
        select(EventOutbox)
        .where(EventOutbox.status == "PENDING")
        .order_by(EventOutbox.created_at.asc())
        .limit(DISPATCH_BATCH_SIZE)
    )
    events = list(db.scalars(statement).all())
    if not events:
        return 0

    processed = 0
    for event in events:
        success = dispatch_event(client, event)
        if success:
            event.status = "PUBLISHED"
            event.published_at = datetime.now(timezone.utc)
            event.error_message = None
        else:
            event.retry_count += 1
            if event.retry_count >= 5:
                event.status = "FAILED"
                event.error_message = "Exceeded maximum retry limit (5)."
            else:
                event.error_message = "Temporary dispatch failure."
        processed += 1

    db.commit()
    return processed


def run_worker():
    logger.info("Starting DockAppointmentScheduling Outbox Dispatcher Worker...")
    with httpx.Client() as client:
        while True:
            with SessionLocal() as db:
                try:
                    count = process_pending_outbox_events(db, client)
                    if count > 0:
                        logger.info(f"Processed {count} outbox events.")
                except Exception as exc:
                    logger.error(f"Error in outbox worker loop: {exc}")
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_worker()
