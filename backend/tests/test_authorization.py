from datetime import datetime, timedelta, timezone
import pytest
from app.models.carrier import Carrier
from app.models.carrier_user import CarrierUser
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser
from app.models.dock import Dock
from app.models.appointment import Appointment
from app.models.user import User
from app.core.security import hash_password


def test_carrier_cannot_access_other_carrier_data(
    client, db, carrier_user_and_carrier, carrier_token
):
    # Create second carrier and appointment
    other_carrier = Carrier(
        company_name="Other Secret Carrier",
        registration_number="REG-OTHER-99",
        contact_email="other@test.com",
        country="Hungary",
        is_active=True,
    )
    wh = Warehouse(
        name="Test WH",
        code="WH-AUTH-1",
        address="Addr 1",
        city="Budapest",
        postal_code="1000",
        country="Hungary",
        is_active=True,
    )
    db.add_all([other_carrier, wh])
    db.flush()

    other_user = User(
        email="other_dispatcher@test.com",
        hashed_password=hash_password("Pass123!"),
        full_name="Other Dispatcher",
        role="CARRIER",
        is_active=True,
    )
    db.add(other_user)
    db.flush()

    db.add(CarrierUser(user_id=other_user.id, carrier_id=other_carrier.id))

    appt = Appointment(
        reference_number="APT-OTHER-SECRET",
        carrier_id=other_carrier.id,
        warehouse_id=wh.id,
        created_by=other_user.id,
        scheduled_start=datetime.now(timezone.utc) + timedelta(days=1),
        scheduled_end=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
        status="PENDING",
        vehicle_registration="XYZ-999",
        vehicle_type="TRUCK",
        cargo_type="CONFIDENTIAL",
    )
    db.add(appt)
    db.commit()

    # Carrier 1 tries to access Carrier 2's appointment
    headers = {"Authorization": f"Bearer {carrier_token}"}
    resp = client.get(f"/api/v1/appointments/{appt.id}", headers=headers)
    assert resp.status_code == 403

    # Carrier 1 tries to get other carrier info
    resp_carrier = client.get(f"/api/v1/carriers/{other_carrier.id}", headers=headers)
    assert resp_carrier.status_code == 403

    # Carrier 1 tries to create appointment for Carrier 2
    create_payload = {
        "carrier_id": other_carrier.id,
        "warehouse_id": wh.id,
        "scheduled_start": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        "scheduled_end": (datetime.now(timezone.utc) + timedelta(days=2, hours=1)).isoformat(),
        "vehicle_registration": "ABC-111",
        "vehicle_type": "TRUCK",
        "cargo_type": "GENERAL",
    }
    resp_create = client.post("/api/v1/appointments/", json=create_payload, headers=headers)
    assert resp_create.status_code == 403


def test_carrier_cannot_access_admin_endpoints(client, carrier_token):
    headers = {"Authorization": f"Bearer {carrier_token}"}
    # Carrier cannot create warehouse
    resp_wh = client.post(
        "/api/v1/warehouses/",
        json={"name": "Hacked WH", "code": "WH-HACK", "address": "X", "city": "Y", "postal_code": "1", "country": "H"},
        headers=headers,
    )
    assert resp_wh.status_code == 403

    # Carrier cannot list users
    resp_users = client.get("/api/v1/users/", headers=headers)
    assert resp_users.status_code == 403


def test_warehouse_manager_scoped_to_assigned_warehouse(
    client, db, warehouse_manager_user_and_wh, warehouse_manager_token
):
    # Create second warehouse not assigned to this manager
    other_wh = Warehouse(
        name="Unassigned WH",
        code="WH-UNASSIGNED",
        address="Unassigned St",
        city="Debrecen",
        postal_code="4000",
        country="Hungary",
        is_active=True,
    )
    db.add(other_wh)
    db.commit()

    headers = {"Authorization": f"Bearer {warehouse_manager_token}"}
    resp = client.get(f"/api/v1/warehouses/{other_wh.id}", headers=headers)
    assert resp.status_code == 403


def test_auth_me_returns_rich_context(
    client, carrier_user_and_carrier, carrier_token
):
    headers = {"Authorization": f"Bearer {carrier_token}"}
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == carrier_user_and_carrier["user"].email
    assert data["role"] == "CARRIER"
    assert data["carrier"]["id"] == carrier_user_and_carrier["carrier"].id
    assert data["carrier"]["company_name"] == carrier_user_and_carrier["carrier"].company_name
