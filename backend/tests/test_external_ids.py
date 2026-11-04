import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import select
from app.models.appointment import Appointment
from app.models.carrier import Carrier
from app.models.dock import Dock
from app.models.warehouse import Warehouse


def test_appointment_and_carrier_external_uuids(client, db, admin_token):
    """Verify that newly created appointments receive auto-generated UUIDs and carriers store external UUIDs."""
    headers = {"Authorization": f"Bearer {admin_token}"}

    carrier = Carrier(
        company_name="UUID Carrier Co",
        registration_number="UUID-999",
        contact_email="carrier@uuid.com",
        country="Hungary",
        is_active=True,
    )
    warehouse = Warehouse(
        name="UUID Hub",
        code="WH-UUID",
        address="123 Test Ave",
        city="Budapest",
        postal_code="1024",
        country="Hungary",
        timezone="Europe/Budapest",
        is_active=True,
    )
    db.add_all([carrier, warehouse])
    db.commit()
    db.refresh(carrier)
    db.refresh(warehouse)

    carrier_id = carrier.id
    warehouse_id = warehouse.id

    # 1. Check carrier external_carrier_id
    external_carrier_uuid = str(uuid.uuid4())
    carrier = db.get(Carrier, carrier_id)
    carrier.external_carrier_id = external_carrier_uuid
    db.commit()
    db.refresh(carrier)

    assert carrier.external_carrier_id == external_carrier_uuid

    # 2. Create appointment via API
    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start + timedelta(hours=1)

    payload = {
        "carrier_id": carrier_id,
        "warehouse_id": warehouse_id,
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
        "vehicle_registration": "EXT-UUID-99",
        "vehicle_type": "Truck",
        "cargo_type": "Standard Pallets",
    }

    res = client.post("/api/v1/appointments/", json=payload, headers=headers)
    assert res.status_code == 201
    created_id = res.json()["id"]

    # 3. Verify in DB that appointment_id UUID was generated
    db_appointment = db.get(Appointment, created_id)
    assert db_appointment is not None
    assert db_appointment.appointment_id is not None
    # Validate UUID format
    parsed_uuid = uuid.UUID(db_appointment.appointment_id)
    assert str(parsed_uuid) == db_appointment.appointment_id
