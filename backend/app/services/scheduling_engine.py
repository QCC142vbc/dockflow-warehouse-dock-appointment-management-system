
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.dock import Dock
from app.models.dock_capability import DockCapability
from app.models.dock_unavailability import DockUnavailability


BLOCKING_STATUSES = {
    "PENDING",
    "CONFIRMED",
    "CHECKED_IN",
    "ARRIVED",
    "IN_PROGRESS",
}


@dataclass(frozen=True)
class SchedulingConflict:
    code: str
    message: str
    resource_id: int | None = None


def normalize_datetime(value: datetime) -> datetime:
    """
    Normalize a datetime to UTC.

    Naive datetimes loaded from SQLite are treated as UTC.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def validate_time_interval(
    start_time: datetime,
    end_time: datetime,
) -> None:
    """
    Validate the requested appointment interval.
    """
    if start_time.tzinfo is None or end_time.tzinfo is None:
        raise ValueError("Appointment datetimes must be timezone-aware.")

    if normalize_datetime(end_time) <= normalize_datetime(start_time):
        raise ValueError("Appointment end time must be after start time.")


def find_dock_conflicts(
    db: Session,
    dock_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_appointment_id: int | None = None,
    vehicle_length: float | None = None,
    vehicle_weight: float | None = None,
    required_capabilities: list[str] | None = None,
) -> list[SchedulingConflict]:
    """
    Find scheduling conflicts for a specific dock.

    Checks:
    - Dock existence
    - Dock active status
    - Vehicle length/weight compatibility against dock limits
    - Dock capabilities against required capabilities
    - Existing appointments
    - Dock unavailability periods

    The interval uses half-open semantics:
    [start_time, end_time)

    Therefore, one appointment may start exactly when
    another appointment ends.
    """
    validate_time_interval(start_time, end_time)

    start_utc = normalize_datetime(start_time)
    end_utc = normalize_datetime(end_time)

    conflicts: list[SchedulingConflict] = []

    dock = db.get(Dock, dock_id)

    if dock is None:
        return [
            SchedulingConflict(
                code="DOCK_NOT_FOUND",
                message="The requested dock does not exist.",
                resource_id=dock_id,
            )
        ]

    if not dock.is_active:
        return [
            SchedulingConflict(
                code="DOCK_INACTIVE",
                message="The requested dock is inactive.",
                resource_id=dock_id,
            )
        ]

    # Vehicle dimensions compatibility
    if (
        vehicle_length is not None
        and dock.max_vehicle_length is not None
        and vehicle_length > dock.max_vehicle_length
    ):
        conflicts.append(
            SchedulingConflict(
                code="VEHICLE_LENGTH_EXCEEDED",
                message=(
                    f"Vehicle length ({vehicle_length}m) exceeds dock maximum "
                    f"capacity ({dock.max_vehicle_length}m)."
                ),
                resource_id=dock_id,
            )
        )

    if (
        vehicle_weight is not None
        and dock.max_vehicle_weight is not None
        and vehicle_weight > dock.max_vehicle_weight
    ):
        conflicts.append(
            SchedulingConflict(
                code="VEHICLE_WEIGHT_EXCEEDED",
                message=(
                    f"Vehicle/cargo weight ({vehicle_weight}kg) exceeds dock maximum "
                    f"capacity ({dock.max_vehicle_weight}kg)."
                ),
                resource_id=dock_id,
            )
        )

    # Required capabilities check
    if required_capabilities:
        cap_query = select(DockCapability.capability_value).where(
            DockCapability.dock_id == dock_id,
            DockCapability.is_active.is_(True),
        )
        active_caps = set(db.scalars(cap_query).all())
        missing_caps = [
            req for req in required_capabilities if req not in active_caps
        ]
        if missing_caps:
            conflicts.append(
                SchedulingConflict(
                    code="CAPABILITY_MISMATCH",
                    message=(
                        f"Dock lacks required capabilities: {', '.join(missing_caps)}."
                    ),
                    resource_id=dock_id,
                )
            )

    appointment_query = select(Appointment).where(
        Appointment.dock_id == dock_id,
        Appointment.status.in_(BLOCKING_STATUSES),
    )

    if exclude_appointment_id is not None:
        appointment_query = appointment_query.where(
            Appointment.id != exclude_appointment_id
        )

    appointments = db.scalars(appointment_query).all()

    for appointment in appointments:
        existing_start = normalize_datetime(
            appointment.scheduled_start
        )
        existing_end = normalize_datetime(
            appointment.scheduled_end
        )

        overlaps = (
            start_utc < existing_end
            and end_utc > existing_start
        )

        if overlaps:
            conflicts.append(
                SchedulingConflict(
                    code="APPOINTMENT_OVERLAP",
                    message=(
                        "The dock already has an appointment "
                        "during the requested time interval."
                    ),
                    resource_id=appointment.id,
                )
            )

    unavailability_query = select(DockUnavailability).where(
        DockUnavailability.dock_id == dock_id,
    )

    unavailability_periods = db.scalars(
        unavailability_query
    ).all()

    for period in unavailability_periods:
        unavailable_start = normalize_datetime(
            period.start_time
        )
        unavailable_end = normalize_datetime(
            period.end_time
        )

        overlaps = (
            start_utc < unavailable_end
            and end_utc > unavailable_start
        )

        if overlaps:
            conflicts.append(
                SchedulingConflict(
                    code="DOCK_UNAVAILABLE",
                    message=(
                        "The dock is unavailable during "
                        "the requested time interval."
                    ),
                    resource_id=period.id,
                )
            )

    return conflicts


def is_dock_available(
    db: Session,
    dock_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_appointment_id: int | None = None,
    vehicle_length: float | None = None,
    vehicle_weight: float | None = None,
    required_capabilities: list[str] | None = None,
) -> bool:
    """
    Return True if the dock has no scheduling conflicts.
    """
    conflicts = find_dock_conflicts(
        db=db,
        dock_id=dock_id,
        start_time=start_time,
        end_time=end_time,
        exclude_appointment_id=exclude_appointment_id,
        vehicle_length=vehicle_length,
        vehicle_weight=vehicle_weight,
        required_capabilities=required_capabilities,
    )

    return len(conflicts) == 0


def find_available_docks(
    db: Session,
    warehouse_id: int,
    start_time: datetime,
    end_time: datetime,
    vehicle_length: float | None = None,
    vehicle_weight: float | None = None,
    required_capabilities: list[str] | None = None,
    exclude_appointment_id: int | None = None,
) -> list[Dock]:
    """
    Find all active, conflict-free docks in a warehouse for the given interval.
    """
    statement = (
        select(Dock)
        .where(
            Dock.warehouse_id == warehouse_id,
            Dock.is_active.is_(True),
        )
        .order_by(Dock.dock_code)
    )
    docks = list(db.scalars(statement).all())
    available = []
    for dock in docks:
        conflicts = find_dock_conflicts(
            db=db,
            dock_id=dock.id,
            start_time=start_time,
            end_time=end_time,
            exclude_appointment_id=exclude_appointment_id,
            vehicle_length=vehicle_length,
            vehicle_weight=vehicle_weight,
            required_capabilities=required_capabilities,
        )
        if not conflicts:
            available.append(dock)
    return available

