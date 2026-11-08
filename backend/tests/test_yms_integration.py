from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM
from app.models.appointment import Appointment
from app.models.carrier import Carrier
from app.models.dock import Dock
from app.models.warehouse import Warehouse


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


def test_yms_service_reads_only_scheduling_owned_records(
    client, db, admin_user, monkeypatch
):
    headers = yms_headers(monkeypatch)
    warehouse = Warehouse(
        name="North Hub",
        code="NORTH",
        address="1 Main Road",
        city="Budapest",
        postal_code="1000",
        country="Hungary",
        timezone="Europe/Budapest",
        external_warehouse_id=str(uuid4()),
        is_active=True,
    )
    carrier = Carrier(
        company_name="North Freight",
        registration_number="REG-NORTH",
        contact_email="dispatch@example.test",
        country="Hungary",
        external_carrier_id=str(uuid4()),
        is_active=True,
    )
    db.add_all([warehouse, carrier])
    db.flush()
    dock = Dock(
        warehouse_id=warehouse.id,
        dock_code="D-10",
        name="Dock 10",
        external_dock_id=str(uuid4()),
        is_active=True,
    )
    db.add(dock)
    db.flush()
    appointment_id = str(uuid4())
    appointment = Appointment(
        appointment_id=appointment_id,
        reference_number="AP-NORTH-10",
        carrier_id=carrier.id,
        warehouse_id=warehouse.id,
        dock_id=dock.id,
        created_by=admin_user.id,
        scheduled_start=datetime.now(timezone.utc) + timedelta(hours=1),
        scheduled_end=datetime.now(timezone.utc) + timedelta(hours=2),
        status="CONFIRMED",
        vehicle_registration="ABC123",
        vehicle_type="Truck",
        cargo_type="Pallets",
    )
    db.add(appointment)
    db.commit()

    reference = client.get(
        f"/api/v1/integration/yms/appointments/{appointment_id}",
        headers=headers,
    )
    assert reference.status_code == 200
    data = reference.json()
    assert data["appointment_id"] == appointment_id
    assert data["external_warehouse_id"] == warehouse.external_warehouse_id
    assert data["external_dock_id"] == dock.external_dock_id
    assert data["vehicle_registration"] == "ABC123"

    warehouses = client.get("/api/v1/integration/yms/warehouses", headers=headers)
    assert warehouses.status_code == 200
    assert warehouses.json()[0]["external_warehouse_id"] == warehouse.external_warehouse_id

    docks = client.get(
        f"/api/v1/integration/yms/warehouses/{warehouse.external_warehouse_id}/docks",
        headers=headers,
    )
    assert docks.status_code == 200
    assert docks.json()[0]["external_dock_id"] == dock.external_dock_id


def test_yms_read_requires_a_scoped_service_token(client, monkeypatch):
    headers = yms_headers(monkeypatch)
    bad_token = jwt.encode(
        {
            "sub": settings.YMS_SERVICE_AUTH_ISSUER,
            "scope": "yms:write",
            "iss": settings.YMS_SERVICE_AUTH_ISSUER,
            "aud": settings.YMS_SERVICE_AUTH_AUDIENCE,
        },
        settings.YMS_SERVICE_AUTH_SECRET,
        algorithm=ALGORITHM,
    )
    response = client.get(
        "/api/v1/integration/yms/warehouses",
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert response.status_code == 403
    missing = client.get("/api/v1/integration/yms/warehouses")
    assert missing.status_code == 401
