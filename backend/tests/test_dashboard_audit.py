from datetime import datetime, timedelta, timezone
from app.models.carrier import Carrier
from app.models.warehouse import Warehouse
from app.models.dock import Dock
from app.models.appointment import Appointment


def test_dashboard_metrics_calculation(client, db, admin_token, admin_user):
    wh = Warehouse(
        name="KPI Test WH",
        code="WH-KPI",
        address="KPI St 1",
        city="Budapest",
        postal_code="1000",
        country="Hungary",
        is_active=True,
    )
    c = Carrier(
        company_name="KPI Carrier",
        registration_number="KPI-REG-1",
        contact_email="kpi@test.com",
        country="Hungary",
        is_active=True,
    )
    db.add_all([wh, c])
    db.flush()

    d = Dock(
        warehouse_id=wh.id,
        dock_code="KPI-DK-01",
        name="KPI Dock",
        is_active=True,
    )
    db.add(d)
    db.flush()

    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(hours=2)

    appt1 = Appointment(
        reference_number="APT-KPI-1",
        carrier_id=c.id,
        warehouse_id=wh.id,
        dock_id=d.id,
        created_by=admin_user.id,
        scheduled_start=start,
        scheduled_end=end,
        status="CONFIRMED",
        vehicle_registration="KPI-001",
        vehicle_type="TRUCK",
        cargo_type="GENERAL",
    )
    appt2 = Appointment(
        reference_number="APT-KPI-2",
        carrier_id=c.id,
        warehouse_id=wh.id,
        created_by=admin_user.id,
        scheduled_start=start + timedelta(hours=3),
        scheduled_end=start + timedelta(hours=4),
        status="PENDING",
        vehicle_registration="KPI-002",
        vehicle_type="TRUCK",
        cargo_type="GENERAL",
    )
    db.add_all([appt1, appt2])
    db.commit()

    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/api/v1/dashboard/metrics", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_appointments"] >= 2
    assert data["confirmed_appointments"] >= 1
    assert data["pending_appointments"] >= 1
    assert "daily_volume" in data
    assert data["total_docks"] >= 1


def test_dock_availability_endpoint(client, db, admin_token, admin_user):
    wh = Warehouse(
        name="Avail WH",
        code="WH-AVAIL",
        address="Avail St",
        city="Budapest",
        postal_code="1000",
        country="Hungary",
        is_active=True,
    )
    db.add(wh)
    db.flush()

    dock = Dock(
        warehouse_id=wh.id,
        dock_code="AV-DK-01",
        name="Avail Bay",
        is_active=True,
    )
    db.add(dock)
    db.commit()

    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start + timedelta(hours=1)

    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get(
        "/api/v1/docks/availability",
        params={
            "warehouse_id": wh.id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers=headers,
    )
    assert resp.status_code == 200
    docks = resp.json()
    assert len(docks) == 1
    assert docks[0]["dock_code"] == "AV-DK-01"


def test_audit_logs_endpoint(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.get("/api/v1/audit-logs/", headers=headers)
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)
