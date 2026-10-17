
from datetime import datetime, timedelta, timezone

import pytest

from app.models.appointment import Appointment
from app.models.carrier import Carrier
from app.models.dock import Dock
from app.models.dock_unavailability import DockUnavailability
from app.models.user import User
from app.models.warehouse import Warehouse

from app.services.scheduling_engine import (
    find_dock_conflicts,
    is_dock_available,
    validate_time_interval,
)


@pytest.fixture
def scheduling_resources(db):
    user = User(
        email="scheduler@test.com",
        hashed_password="test-hash",
        full_name="Test Scheduler",
        role="ADMIN",
        is_active=True,
    )

    carrier = Carrier(
        company_name="Test Transport",
        registration_number="TEST-001",
        contact_email="transport@test.com",
        country="Hungary",
        is_active=True,
    )

    warehouse = Warehouse(
        name="Test Warehouse",
        code="WH-TEST",
        address="Test Street 1",
        city="Budapest",
        postal_code="1000",
        country="Hungary",
        timezone="Europe/Budapest",
        is_active=True,
    )

    db.add_all([user, carrier, warehouse])
    db.flush()

    dock = Dock(
        warehouse_id=warehouse.id,
        dock_code="DOCK-01",
        name="Test Dock",
        is_active=True,
    )

    db.add(dock)
    db.commit()

    return {
        "user": user,
        "carrier": carrier,
        "warehouse": warehouse,
        "dock": dock,
    }


def create_appointment(
    db,
    resources,
    start_time,
    end_time,
    status="CONFIRMED",
):
    appointment = Appointment(
        reference_number=f"TEST-{start_time.timestamp()}",
        carrier_id=resources["carrier"].id,
        warehouse_id=resources["warehouse"].id,
        dock_id=resources["dock"].id,
        created_by=resources["user"].id,
        scheduled_start=start_time,
        scheduled_end=end_time,
        status=status,
        vehicle_registration="ABC-123",
        vehicle_type="TRUCK",
        cargo_type="GENERAL",
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return appointment


@pytest.fixture
def time_range():
    start = datetime(
        2026, 10, 12, 10, 0,
        tzinfo=timezone.utc,
    )

    end = start + timedelta(hours=1)

    return start, end


def test_available_dock_returns_no_conflicts(
    db,
    scheduling_resources,
    time_range,
):
    start, end = time_range

    conflicts = find_dock_conflicts(
        db,
        scheduling_resources["dock"].id,
        start,
        end,
    )

    assert conflicts == []

    assert is_dock_available(
        db,
        scheduling_resources["dock"].id,
        start,
        end,
    ) is True


def test_overlapping_appointment_is_detected(
    db,
    scheduling_resources,
    time_range,
):
    start, end = time_range

    create_appointment(
        db,
        scheduling_resources,
        start,
        end,
    )

    conflicts = find_dock_conflicts(
        db,
        scheduling_resources["dock"].id,
        start + timedelta(minutes=30),
        end + timedelta(minutes=30),
    )

    assert len(conflicts) == 1
    assert conflicts[0].code == "APPOINTMENT_OVERLAP"


def test_adjacent_appointments_do_not_conflict(
    db,
    scheduling_resources,
    time_range,
):
    start, end = time_range

    create_appointment(
        db,
        scheduling_resources,
        start,
        end,
    )

    conflicts = find_dock_conflicts(
        db,
        scheduling_resources["dock"].id,
        end,
        end + timedelta(hours=1),
    )

    assert conflicts == []


def test_inactive_dock_is_rejected(
    db,
    scheduling_resources,
    time_range,
):
    start, end = time_range

    dock = scheduling_resources["dock"]
    dock.is_active = False
    db.commit()

    conflicts = find_dock_conflicts(
        db,
        dock.id,
        start,
        end,
    )

    assert len(conflicts) == 1
    assert conflicts[0].code == "DOCK_INACTIVE"


def test_dock_unavailability_is_detected(
    db,
    scheduling_resources,
    time_range,
):
    start, end = time_range

    unavailability = DockUnavailability(
        dock_id=scheduling_resources["dock"].id,
        reason_type="MAINTENANCE",
        description="Scheduled maintenance",
        start_time=start + timedelta(minutes=15),
        end_time=end + timedelta(minutes=15),
        reported_by=scheduling_resources["user"].id,
    )

    db.add(unavailability)
    db.commit()

    conflicts = find_dock_conflicts(
        db,
        scheduling_resources["dock"].id,
        start,
        end,
    )

    assert len(conflicts) == 1
    assert conflicts[0].code == "DOCK_UNAVAILABLE"


def test_own_appointment_can_be_excluded(
    db,
    scheduling_resources,
    time_range,
):
    start, end = time_range

    appointment = create_appointment(
        db,
        scheduling_resources,
        start,
        end,
    )

    conflicts = find_dock_conflicts(
        db,
        scheduling_resources["dock"].id,
        start,
        end,
        exclude_appointment_id=appointment.id,
    )

    assert conflicts == []


def test_non_blocking_status_does_not_cause_conflict(
    db,
    scheduling_resources,
    time_range,
):
    start, end = time_range

    create_appointment(
        db,
        scheduling_resources,
        start,
        end,
        status="CANCELLED",
    )

    conflicts = find_dock_conflicts(
        db,
        scheduling_resources["dock"].id,
        start,
        end,
    )

    assert conflicts == []


def test_nonexistent_dock_is_rejected(
    db,
    time_range,
):
    start, end = time_range

    conflicts = find_dock_conflicts(
        db,
        dock_id=999999,
        start_time=start,
        end_time=end,
    )

    assert len(conflicts) == 1
    assert conflicts[0].code == "DOCK_NOT_FOUND"


def test_invalid_time_interval_is_rejected():
    start = datetime(
        2026, 10, 12, 12, 0,
        tzinfo=timezone.utc,
    )

    end = start - timedelta(hours=1)

    with pytest.raises(ValueError):
        validate_time_interval(start, end)


def test_naive_datetime_is_rejected():
    start = datetime(2026, 10, 12, 10, 0)
    end = datetime(2026, 10, 12, 11, 0)

    with pytest.raises(ValueError):
        validate_time_interval(start, end)


def test_vehicle_length_exceeded_is_detected(db, scheduling_resources, time_range):
    start, end = time_range
    dock = scheduling_resources["dock"]
    dock.max_vehicle_length = 12.0
    db.commit()

    conflicts = find_dock_conflicts(
        db=db,
        dock_id=dock.id,
        start_time=start,
        end_time=end,
        vehicle_length=16.5,
    )
    assert len(conflicts) == 1
    assert conflicts[0].code == "VEHICLE_LENGTH_EXCEEDED"


def test_vehicle_weight_exceeded_is_detected(db, scheduling_resources, time_range):
    start, end = time_range
    dock = scheduling_resources["dock"]
    dock.max_vehicle_weight = 20000.0
    db.commit()

    conflicts = find_dock_conflicts(
        db=db,
        dock_id=dock.id,
        start_time=start,
        end_time=end,
        vehicle_weight=24000.0,
    )
    assert len(conflicts) == 1
    assert conflicts[0].code == "VEHICLE_WEIGHT_EXCEEDED"


def test_capability_mismatch_is_detected(db, scheduling_resources, time_range):
    from app.models.dock_capability import DockCapability

    start, end = time_range
    dock = scheduling_resources["dock"]
    cap = DockCapability(
        dock_id=dock.id,
        capability_type="TEMPERATURE",
        capability_value="AMBIENT",
        is_active=True,
    )
    db.add(cap)
    db.commit()

    # Require COLD_CHAIN which dock does not have
    conflicts = find_dock_conflicts(
        db=db,
        dock_id=dock.id,
        start_time=start,
        end_time=end,
        required_capabilities=["COLD_CHAIN"],
    )
    assert len(conflicts) == 1
    assert conflicts[0].code == "CAPABILITY_MISMATCH"

