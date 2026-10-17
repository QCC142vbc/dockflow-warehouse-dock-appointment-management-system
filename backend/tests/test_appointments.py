
from datetime import datetime, timedelta, timezone

import pytest

from app.models.appointment import Appointment
from app.models.carrier import Carrier
from app.models.carrier_user import CarrierUser
from app.models.dock import Dock
from app.models.user import User
from app.models.warehouse import Warehouse


@pytest.fixture
def appointment_resources(db, admin_token, admin_user):
    carrier = Carrier(
        company_name="Integration Transport",
        registration_number="INT-001",
        contact_email="integration@test.com",
        country="Hungary",
        is_active=True,
    )

    warehouse = Warehouse(
        name="Integration Warehouse",
        code="WH-INT",
        address="Integration Street 1",
        city="Budapest",
        postal_code="1000",
        country="Hungary",
        timezone="Europe/Budapest",
        is_active=True,
    )

    second_warehouse = Warehouse(
        name="Second Warehouse",
        code="WH-INT-2",
        address="Integration Street 2",
        city="Budapest",
        postal_code="1001",
        country="Hungary",
        timezone="Europe/Budapest",
        is_active=True,
    )

    db.add_all([carrier, warehouse, second_warehouse])
    db.flush()

    dock = Dock(
        warehouse_id=warehouse.id,
        dock_code="INT-DOCK-01",
        name="Integration Dock",
        is_active=True,
    )

    second_dock = Dock(
        warehouse_id=second_warehouse.id,
        dock_code="INT-DOCK-02",
        name="Second Integration Dock",
        is_active=True,
    )

    inactive_dock = Dock(
        warehouse_id=warehouse.id,
        dock_code="INT-DOCK-03",
        name="Inactive Integration Dock",
        is_active=False,
    )

    db.add_all([dock, second_dock, inactive_dock])
    db.commit()

    return {
        "carrier": carrier,
        "warehouse": warehouse,
        "second_warehouse": second_warehouse,
        "dock": dock,
        "second_dock": second_dock,
        "inactive_dock": inactive_dock,
        "token": admin_token,
        "user": admin_user,
    }


@pytest.fixture
def appointment_payload(appointment_resources):
    start = datetime(
        2026, 10, 20, 10, 0,
        tzinfo=timezone.utc,
    )

    end = start + timedelta(hours=1)

    return {
        "carrier_id": appointment_resources["carrier"].id,
        "warehouse_id": appointment_resources["warehouse"].id,
        "dock_id": appointment_resources["dock"].id,
        "scheduled_start": start.isoformat(),
        "scheduled_end": end.isoformat(),
        "vehicle_registration": "ABC-123",
        "vehicle_type": "TRUCK",
        "cargo_type": "GENERAL",
        "cargo_weight_kg": 12000,
    }


@pytest.fixture
def auth_headers(appointment_resources):
    return {
        "Authorization": (
            f"Bearer {appointment_resources['token']}"
        )
    }


def create_appointment(
    client,
    payload,
    headers,
):
    return client.post(
        "/api/v1/appointments/",
        json=payload,
        headers=headers,
    )


def test_create_appointment_success(
    client,
    appointment_payload,
    auth_headers,
):
    response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "PENDING"
    assert data["reference_number"].startswith("APT-")
    assert data["dock_id"] == appointment_payload["dock_id"]


def test_create_appointment_on_occupied_dock_returns_conflict(
    client,
    appointment_payload,
    auth_headers,
):
    first_response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert first_response.status_code == 201

    second_response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert second_response.status_code == 409
    assert (
        second_response.json()["detail"]["conflicts"][0]["code"]
        == "APPOINTMENT_OVERLAP"
    )


def test_create_appointment_on_inactive_dock_is_rejected(
    client,
    appointment_resources,
    appointment_payload,
    auth_headers,
):
    appointment_payload["dock_id"] = (
        appointment_resources["inactive_dock"].id
    )

    response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]["conflicts"][0]["code"]
        == "DOCK_INACTIVE"
    )


def test_create_appointment_with_wrong_warehouse_dock_is_rejected(
    client,
    appointment_resources,
    appointment_payload,
    auth_headers,
):
    appointment_payload["dock_id"] = (
        appointment_resources["second_dock"].id
    )

    response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert response.status_code == 422


def test_update_appointment_to_overlapping_time_returns_conflict(
    client,
    appointment_payload,
    appointment_resources,
    auth_headers,
):
    first_response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert first_response.status_code == 201

    second_payload = appointment_payload.copy()
    second_payload["dock_id"] = None

    second_response = create_appointment(
        client,
        second_payload,
        auth_headers,
    )

    assert second_response.status_code == 201

    appointment_id = second_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={
            "dock_id": appointment_resources["dock"].id,
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 409


def test_update_appointment_can_keep_own_dock(
    client,
    appointment_payload,
    auth_headers,
):
    create_response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert create_response.status_code == 201

    appointment_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/appointments/{appointment_id}",
        json={
            "notes": "Updated integration test note",
        },
        headers=auth_headers,
    )

    assert update_response.status_code == 200
    assert (
        update_response.json()["notes"]
        == "Updated integration test note"
    )


def test_confirmation_without_dock_is_rejected(
    client,
    appointment_payload,
    auth_headers,
):
    appointment_payload["dock_id"] = None

    create_response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert create_response.status_code == 201

    appointment_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={"status": "CONFIRMED"},
        headers=auth_headers,
    )

    assert response.status_code == 409


def test_appointment_can_be_cancelled(
    client,
    appointment_payload,
    auth_headers,
):
    create_response = create_appointment(
        client,
        appointment_payload,
        auth_headers,
    )

    assert create_response.status_code == 201

    appointment_id = create_response.json()["id"]

    response = client.patch(
        f"/api/v1/appointments/{appointment_id}/status",
        json={
            "status": "CANCELLED",
            "reason": "Integration test cancellation",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
