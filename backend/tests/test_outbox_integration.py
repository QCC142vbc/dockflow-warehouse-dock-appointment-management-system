import uuid
from datetime import datetime, timezone
import pytest
from jose import jwt
from app.models.appointment import Appointment
from app.models.carrier import Carrier
from app.models.warehouse import Warehouse
from app.models.event_outbox import EventOutbox
from outbox_worker import process_pending_outbox_events
from app.core.config import settings


class MockResponse:
    def __init__(self, status_code=201, data=None):
        self.status_code = status_code
        self._data = data or {}
        self.text = "OK"

    def json(self):
        return self._data


class MockHttpClient:
    def __init__(self, status_code=201):
        self.status_code = status_code
        self.posted = []

    def post(self, url, json=None, headers=None, timeout=None):
        self.posted.append({"url": url, "payload": json, "headers": headers})
        return MockResponse(self.status_code, {"synced": True})


def test_outbox_event_creation_and_worker_dispatch(client, db, admin_token, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "SERVICE_AUTH_SECRET", "s" * 40)
    headers = {"Authorization": f"Bearer {admin_token}"}

    carrier = Carrier(
        company_name="Outbox Carrier Express",
        registration_number="OBX-001",
        contact_email="outbox@test.com",
        country="Hungary",
        is_active=True,
    )
    warehouse = Warehouse(
        name="Outbox Hub",
        code="WH-OBX",
        address="Outbox Street 1",
        city="Budapest",
        postal_code="1025",
        country="Hungary",
        timezone="Europe/Budapest",
        is_active=True,
    )
    db.add_all([carrier, warehouse])
    db.commit()

    # 1. Create appointment via API
    payload = {
        "carrier_id": carrier.id,
        "warehouse_id": warehouse.id,
        "scheduled_start": datetime.now(timezone.utc).isoformat(),
        "scheduled_end": (datetime.now(timezone.utc)).isoformat(),
        "vehicle_registration": "OBX-TRUCK-01",
        "vehicle_type": "Truck",
        "cargo_type": "Fragile Logistics",
    }
    res = client.post("/api/v1/appointments/", json=payload, headers=headers)
    assert res.status_code == 201

    # 2. Verify an outbox event was recorded in DB
    pending_events = (
        db.query(EventOutbox)
        .filter(EventOutbox.event_type == "appointment.created")
        .all()
    )
    assert len(pending_events) >= 1
    event = pending_events[-1]
    assert event.status == "PENDING"
    assert event.payload["vehicle_registration"] == "OBX-TRUCK-01"

    # 3. Simulate outbox worker dispatching the event
    mock_client = MockHttpClient(status_code=201)
    processed = process_pending_outbox_events(db, mock_client)
    assert processed >= 1
    assert len(mock_client.posted) >= 1
    assert mock_client.posted[0]["url"].endswith("/sync/appointment")
    service_token = mock_client.posted[0]["headers"]["Authorization"].removeprefix("Bearer ")
    claims = jwt.decode(
        service_token,
        settings.SERVICE_AUTH_SECRET,
        algorithms=["HS256"],
        issuer=settings.SERVICE_AUTH_ISSUER,
        audience=settings.SERVICE_AUTH_AUDIENCE,
    )
    assert claims["scope"] == "integration:write"

    # 4. Verify status changed to PUBLISHED
    db.refresh(event)
    assert event.status == "PUBLISHED"
    assert event.published_at is not None
