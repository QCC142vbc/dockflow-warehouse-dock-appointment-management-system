from datetime import datetime, timedelta, timezone

from app.models.appointment import Appointment
from app.models.appointment_event import AppointmentEvent
from app.models.carrier import Carrier
from app.models.dock import Dock
from app.models.warehouse import Warehouse


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_empty_dashboard_does_not_invent_dock_utilization(client, admin_token):
    response = client.get("/api/v1/dashboard/metrics", headers=headers(admin_token))

    assert response.status_code == 200
    data = response.json()
    assert data["total_appointments"] == 0
    assert data["total_docks"] == 0
    assert data["active_docks"] == 0
    assert data["dock_utilization_percent"] is None
    assert data["daily_volume"] == []


def test_warehouse_and_dock_manual_crud_and_safe_deactivation(client, admin_token):
    auth = headers(admin_token)
    warehouse_response = client.post(
        "/api/v1/warehouses/",
        headers=auth,
        json={
            "name": "Manual Entry Warehouse",
            "code": "MANUAL-WH",
            "address": "1 Operations Way",
            "city": "Budapest",
            "postal_code": "1000",
            "country": "Hungary",
            "timezone": "Europe/Budapest",
        },
    )
    assert warehouse_response.status_code == 201
    warehouse_id = warehouse_response.json()["id"]

    updated_warehouse = client.patch(
        f"/api/v1/warehouses/{warehouse_id}",
        headers=auth,
        json={"name": "Edited Manual Warehouse", "country": "Austria"},
    )
    assert updated_warehouse.status_code == 200
    assert updated_warehouse.json()["name"] == "Edited Manual Warehouse"
    assert updated_warehouse.json()["country"] == "Austria"

    dock_response = client.post(
        "/api/v1/docks/",
        headers=auth,
        json={
            "warehouse_id": warehouse_id,
            "dock_code": "MANUAL-D1",
            "name": "Manual Loading Dock",
            "description": "Entered by the administrator",
        },
    )
    assert dock_response.status_code == 201
    dock_id = dock_response.json()["id"]

    duplicate_dock = client.post(
        "/api/v1/docks/",
        headers=auth,
        json={
            "warehouse_id": warehouse_id,
            "dock_code": "MANUAL-D1",
            "name": "Duplicate Dock",
        },
    )
    assert duplicate_dock.status_code == 409

    updated_dock = client.patch(
        f"/api/v1/docks/{dock_id}",
        headers=auth,
        json={"dock_code": "MANUAL-D2", "name": "Edited Loading Dock"},
    )
    assert updated_dock.status_code == 200
    assert updated_dock.json()["dock_code"] == "MANUAL-D2"

    assert client.delete(f"/api/v1/docks/{dock_id}", headers=auth).status_code == 204
    docks = client.get(f"/api/v1/docks/?warehouse_id={warehouse_id}", headers=auth).json()
    assert len(docks) == 1
    assert docks[0]["id"] == dock_id
    assert docks[0]["is_active"] is False

    assert client.delete(f"/api/v1/warehouses/{warehouse_id}", headers=auth).status_code == 204
    warehouses = client.get("/api/v1/warehouses/", headers=auth).json()
    assert next(item for item in warehouses if item["id"] == warehouse_id)["is_active"] is False


def test_appointment_cancel_retains_auditable_record(client, db, admin_token, admin_user):
    warehouse = Warehouse(
        name="History Warehouse",
        code="HISTORY-WH",
        address="History Road 1",
        city="Budapest",
        postal_code="1000",
        country="Hungary",
        timezone="Europe/Budapest",
        is_active=True,
    )
    carrier = Carrier(
        company_name="History Carrier",
        registration_number="HISTORY-CARRIER",
        contact_email="history@example.com",
        country="Hungary",
        is_active=True,
    )
    db.add_all([warehouse, carrier])
    db.flush()
    dock = Dock(
        warehouse_id=warehouse.id,
        dock_code="HISTORY-D1",
        name="History Dock",
        is_active=True,
    )
    db.add(dock)
    db.flush()
    start = datetime.now(timezone.utc) + timedelta(days=2)
    appointment = Appointment(
        reference_number="APT-MANUAL-HISTORY",
        carrier_id=carrier.id,
        warehouse_id=warehouse.id,
        dock_id=dock.id,
        created_by=admin_user.id,
        scheduled_start=start,
        scheduled_end=start + timedelta(hours=1),
        status="PENDING",
        vehicle_registration="HISTORY-1",
        vehicle_type="TRUCK",
        cargo_type="PALLETS",
    )
    db.add(appointment)
    db.commit()
    appointment_id = appointment.id

    response = client.delete(
        f"/api/v1/appointments/{appointment_id}",
        headers=headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert db.get(Appointment, appointment_id) is not None
    event = db.query(AppointmentEvent).filter_by(appointment_id=appointment_id).one()
    assert event.new_status == "CANCELLED"
