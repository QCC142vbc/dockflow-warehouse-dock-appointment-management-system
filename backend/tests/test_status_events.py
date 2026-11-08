from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from sqlalchemy import select

from app.core.config import settings
from app.core.security import ALGORITHM
from app.models.event_outbox import EventOutbox


def yms_headers(monkeypatch):
    secret = "scheduling-yms-test-secret-long-enough-123456"
    monkeypatch.setattr(settings, "YMS_SERVICE_AUTH_SECRET", secret)
    token = jwt.encode(
        {
            "sub": settings.YMS_SERVICE_AUTH_ISSUER,
            "scope": "yms:read",
            "iss": settings.YMS_SERVICE_AUTH_ISSUER,
            "aud": settings.YMS_SERVICE_AUTH_AUDIENCE,
        },
        secret,
        algorithm=ALGORITHM,
    )
    return {"Authorization": f"Bearer {token}"}


def create_reference_data(db):
    from app.models.carrier import Carrier
    from app.models.warehouse import Warehouse

    carrier = Carrier(
        company_name="Status Carrier",
        registration_number="REG-STATUS-1",
        contact_email="status-carrier@test.com",
        country="Germany",
        is_active=True,
    )
    warehouse = Warehouse(
        name="Status Hub",
        code="WH-STS",
        address="Status Street 1",
        city="Győr",
        postal_code="9000",
        country="Hungary",
        timezone="Europe/Budapest",
        is_active=True,
    )
    db.add_all([carrier, warehouse])
    db.commit()
    return carrier, warehouse


def appointment_payload(carrier_id, warehouse_id):
    start = datetime.now(timezone.utc) + timedelta(hours=2)
    return {
        "carrier_id": carrier_id,
        "warehouse_id": warehouse_id,
        "scheduled_start": start.isoformat(),
        "scheduled_end": (start + timedelta(hours=2)).isoformat(),
        "vehicle_registration": "STS-TRUCK-1",
        "vehicle_type": "Truck",
        "cargo_type": "General freight",
        "cargo_weight_kg": 5000,
    }


def test_status_transition_emits_operations_sync_event(client, db, admin_token):
    carrier, warehouse = create_reference_data(db)
    headers = {"Authorization": f"Bearer {admin_token}"}

    created = client.post(
        "/api/v1/appointments/",
        json=appointment_payload(carrier.id, warehouse.id),
        headers=headers,
    )
    assert created.status_code == 201
    appointment = created.json()
    assert appointment["status"] == "PENDING"

    rejected = client.patch(
        f"/api/v1/appointments/{appointment['id']}/status",
        json={"status": "REJECTED", "reason": "Capacity unavailable."},
        headers=headers,
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"

    event = db.scalar(
        select(EventOutbox).where(
            EventOutbox.event_type == "appointment.status_changed"
        )
    )
    assert event is not None
    assert event.status == "PENDING"
    assert event.payload["appointment_id"] == appointment["appointment_id"]
    assert event.payload["reference_number"] == appointment["reference_number"]
    assert event.payload["status"] == "REJECTED"
    assert event.payload["previous_status"] == "PENDING"
    assert event.payload["status_changed_at"]
    assert event.payload["external_carrier_id"].startswith("scheduling:carrier:")
    assert event.payload["external_warehouse_id"].startswith("scheduling:warehouse:")


def test_reference_number_resolves_for_yms_lookup(client, db, admin_token, monkeypatch):
    carrier, warehouse = create_reference_data(db)
    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/v1/appointments/",
        json=appointment_payload(carrier.id, warehouse.id),
        headers=headers,
    )
    assert created.status_code == 201
    appointment = created.json()

    resolved = client.get(
        f"/api/v1/integration/yms/appointments/{appointment['reference_number']}",
        headers=yms_headers(monkeypatch),
    )
    assert resolved.status_code == 200
    data = resolved.json()
    assert data["appointment_id"] == appointment["appointment_id"]
    assert data["reference_number"] == appointment["reference_number"]
    assert data["vehicle_registration"] == "STS-TRUCK-1"


def test_carrier_country_persists_through_api(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    created = client.post(
        "/api/v1/carriers/",
        json={
            "company_name": "Country Check Carrier",
            "registration_number": "REG-COUNTRY-UI",
            "contact_email": "country@test.com",
            "country": "Germany",
        },
        headers=headers,
    )
    assert created.status_code == 201
    carrier = created.json()
    assert carrier["country"] == "Germany"

    carriers = client.get("/api/v1/carriers/", headers=headers)
    assert carriers.status_code == 200
    stored = next(item for item in carriers.json() if item["id"] == carrier["id"])
    assert stored["country"] == "Germany"

    updated = client.patch(
        f"/api/v1/carriers/{carrier['id']}",
        json={"country": "Poland"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["country"] == "Poland"

    carriers = client.get("/api/v1/carriers/", headers=headers)
    stored = next(item for item in carriers.json() if item["id"] == carrier["id"])
    assert stored["country"] == "Poland"
