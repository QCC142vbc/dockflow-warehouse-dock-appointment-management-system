from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.appointment import Appointment
from app.models.appointment_event import AppointmentEvent
from app.models.carrier import Carrier
from app.models.carrier_user import CarrierUser
from app.models.dock import Dock
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatusUpdate,
    AppointmentResponse,
    AppointmentStatus,
)
from app.schemas.appointment_event import AppointmentEventResponse
from app.services.audit import log_audit
from app.services.scheduling_engine import (
    BLOCKING_STATUSES,
    find_dock_conflicts,
)


router = APIRouter()


def get_user_carrier_ids(
    db: Session,
    user_id: int,
) -> list[int]:
    statement = select(CarrierUser.carrier_id).where(
        CarrierUser.user_id == user_id
    )
    return list(db.scalars(statement).all())


def get_user_warehouse_ids(
    db: Session,
    user_id: int,
) -> list[int]:
    statement = select(WarehouseUser.warehouse_id).where(
        WarehouseUser.user_id == user_id
    )
    return list(db.scalars(statement).all())


def to_response_dto(db: Session, appointment: Appointment) -> AppointmentResponse:
    resp = AppointmentResponse.model_validate(appointment)

    # Attach display names
    carrier = db.get(Carrier, appointment.carrier_id)
    if carrier:
        resp.carrier_name = carrier.company_name

    warehouse = db.get(Warehouse, appointment.warehouse_id)
    if warehouse:
        resp.warehouse_name = f"{warehouse.name} ({warehouse.code})"

    if appointment.dock_id:
        dock = db.get(Dock, appointment.dock_id)
        if dock:
            resp.dock_code = dock.dock_code

    return resp


def get_accessible_appointment(
    appointment_id: int,
    db: Session,
    current_user: User,
) -> Appointment:
    appointment = db.get(Appointment, appointment_id)

    if appointment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found.",
        )

    if current_user.role == "CARRIER":
        carrier_ids = get_user_carrier_ids(db, current_user.id)

        if appointment.carrier_id not in carrier_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this appointment.",
            )

    elif current_user.role in ("WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
        assigned = get_user_warehouse_ids(db, current_user.id)
        if assigned and appointment.warehouse_id not in assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this appointment for this warehouse.",
            )

    elif current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access appointments.",
        )

    return appointment


def validate_dock_assignment(
    db: Session,
    dock_id: int,
    warehouse_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_appointment_id: int | None = None,
    cargo_weight_kg: float | None = None,
) -> None:
    dock = db.get(Dock, dock_id)

    if dock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock not found.",
        )

    if dock.warehouse_id != warehouse_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The selected dock does not belong to this warehouse.",
        )

    try:
        conflicts = find_dock_conflicts(
            db=db,
            dock_id=dock_id,
            start_time=start_time,
            end_time=end_time,
            exclude_appointment_id=exclude_appointment_id,
            vehicle_weight=cargo_weight_kg,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc

    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "The requested dock is not available.",
                "conflicts": [
                    {
                        "code": conflict.code,
                        "message": conflict.message,
                        "resource_id": conflict.resource_id,
                    }
                    for conflict in conflicts
                ],
            },
        )


@router.get(
    "/",
    response_model=list[AppointmentResponse],
)
def get_appointments(
    warehouse_id: int | None = None,
    carrier_id: int | None = None,
    dock_id: int | None = None,
    appointment_status: AppointmentStatus | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int | None = Query(default=None, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Appointment)

    if current_user.role == "CARRIER":
        carrier_ids = get_user_carrier_ids(db, current_user.id)
        statement = statement.where(
            Appointment.carrier_id.in_(carrier_ids)
        )

    elif current_user.role in (
        "ADMIN",
        "WAREHOUSE_MANAGER",
        "WAREHOUSE_STAFF",
    ):
        if current_user.role in ("WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
            assigned = get_user_warehouse_ids(db, current_user.id)
            if assigned:
                statement = statement.where(Appointment.warehouse_id.in_(assigned))

        if carrier_id is not None:
            statement = statement.where(
                Appointment.carrier_id == carrier_id
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view appointments.",
        )

    if warehouse_id is not None:
        statement = statement.where(
            Appointment.warehouse_id == warehouse_id
        )

    if dock_id is not None:
        statement = statement.where(
            Appointment.dock_id == dock_id
        )

    if appointment_status is not None:
        statement = statement.where(
            Appointment.status == appointment_status.value
        )

    if start_date is not None:
        statement = statement.where(
            Appointment.scheduled_start >= start_date
        )

    if end_date is not None:
        statement = statement.where(
            Appointment.scheduled_start <= end_date
        )

    statement = statement.order_by(Appointment.scheduled_start.desc())

    if offset:
        statement = statement.offset(offset)
    if limit:
        statement = statement.limit(limit)

    appointments = db.scalars(statement).all()
    return [to_response_dto(db, a) for a in appointments]


@router.get(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = get_accessible_appointment(
        appointment_id,
        db,
        current_user,
    )
    return to_response_dto(db, appointment)


@router.get(
    "/{appointment_id}/events",
    response_model=list[AppointmentEventResponse],
)
def get_appointment_events(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify access first
    get_accessible_appointment(
        appointment_id,
        db,
        current_user,
    )

    statement = (
        select(AppointmentEvent)
        .where(AppointmentEvent.appointment_id == appointment_id)
        .order_by(AppointmentEvent.created_at.asc())
    )
    return list(db.scalars(statement).all())


@router.post(
    "/",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "CARRIER":
        carrier_ids = get_user_carrier_ids(db, current_user.id)

        if appointment_data.carrier_id not in carrier_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot create appointments for this carrier.",
            )

    elif current_user.role not in (
        "ADMIN",
        "WAREHOUSE_MANAGER",
        "WAREHOUSE_STAFF",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to create appointments.",
        )

    carrier = db.get(Carrier, appointment_data.carrier_id)

    if carrier is None or not carrier.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active carrier not found.",
        )

    warehouse = db.get(Warehouse, appointment_data.warehouse_id)
    if warehouse is None or not warehouse.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active warehouse not found.",
        )

    if appointment_data.dock_id is not None:
        validate_dock_assignment(
            db=db,
            dock_id=appointment_data.dock_id,
            warehouse_id=appointment_data.warehouse_id,
            start_time=appointment_data.scheduled_start,
            end_time=appointment_data.scheduled_end,
            cargo_weight_kg=appointment_data.cargo_weight_kg,
        )

    initial_status = (
        appointment_data.status.value
        if appointment_data.status in (AppointmentStatus.DRAFT, AppointmentStatus.PENDING)
        else AppointmentStatus.PENDING.value
    )

    reference_number = f"APT-{uuid4().hex[:10].upper()}"

    data_dict = appointment_data.model_dump()
    data_dict.pop("status", None)

    new_appointment = Appointment(
        **data_dict,
        reference_number=reference_number,
        created_by=current_user.id,
        status=initial_status,
    )

    try:
        db.add(new_appointment)
        db.flush()

        event = AppointmentEvent(
            appointment_id=new_appointment.id,
            changed_by=current_user.id,
            previous_status=None,
            new_status=initial_status,
            event_type="CREATED",
            reason="Appointment created.",
        )
        db.add(event)

        log_audit(
            db=db,
            user_id=current_user.id,
            action="CREATE_APPOINTMENT",
            entity_type="Appointment",
            entity_id=new_appointment.id,
            description=f"Created appointment {reference_number} with status {initial_status}",
            new_values={
                "reference_number": reference_number,
                "carrier_id": new_appointment.carrier_id,
                "warehouse_id": new_appointment.warehouse_id,
                "dock_id": new_appointment.dock_id,
                "status": initial_status,
            },
        )

        db.commit()
        db.refresh(new_appointment)

    except Exception:
        db.rollback()
        raise

    return to_response_dto(db, new_appointment)


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentResponse,
)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = get_accessible_appointment(
        appointment_id,
        db,
        current_user,
    )

    if appointment.status not in (
        AppointmentStatus.DRAFT.value,
        AppointmentStatus.PENDING.value,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft or pending appointments can be edited.",
        )

    update_data = appointment_data.model_dump(exclude_unset=True)

    new_start = update_data.get(
        "scheduled_start",
        appointment.scheduled_start,
    )

    new_end = update_data.get(
        "scheduled_end",
        appointment.scheduled_end,
    )

    new_dock_id = update_data.get(
        "dock_id",
        appointment.dock_id,
    )

    new_weight = update_data.get(
        "cargo_weight_kg",
        appointment.cargo_weight_kg,
    )

    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Appointment end must be after appointment start.",
        )

    if new_dock_id is not None:
        validate_dock_assignment(
            db=db,
            dock_id=new_dock_id,
            warehouse_id=appointment.warehouse_id,
            start_time=new_start,
            end_time=new_end,
            exclude_appointment_id=appointment.id,
            cargo_weight_kg=new_weight,
        )

    old_values = {k: getattr(appointment, k) for k in update_data.keys()}

    try:
        for field, value in update_data.items():
            setattr(appointment, field, value)

        appointment.updated_at = datetime.now(timezone.utc)

        log_audit(
            db=db,
            user_id=current_user.id,
            action="UPDATE_APPOINTMENT",
            entity_type="Appointment",
            entity_id=appointment.id,
            description=f"Updated appointment {appointment.reference_number}",
            old_values=old_values,
            new_values=update_data,
        )

        db.commit()
        db.refresh(appointment)

    except Exception:
        db.rollback()
        raise

    return to_response_dto(db, appointment)


@router.patch(
    "/{appointment_id}/status",
    response_model=AppointmentResponse,
)
def update_appointment_status(
    appointment_id: int,
    status_data: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = get_accessible_appointment(
        appointment_id,
        db,
        current_user,
    )

    new_status = status_data.status.value
    old_status = appointment.status

    allowed_transitions = {
        "DRAFT": ["PENDING", "CANCELLED"],
        "PENDING": ["CONFIRMED", "REJECTED", "CANCELLED"],
        "CONFIRMED": ["CANCELLED", "CHECKED_IN", "NO_SHOW"],
        "CHECKED_IN": ["ARRIVED", "CANCELLED"],
        "ARRIVED": ["IN_PROGRESS"],
        "IN_PROGRESS": ["COMPLETED"],
        "REJECTED": [],
        "CANCELLED": [],
        "COMPLETED": [],
        "NO_SHOW": [],
    }

    if new_status not in allowed_transitions.get(old_status, []):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Transition from {old_status} "
                f"to {new_status} is not allowed."
            ),
        )

    # Permission checks
    if current_user.role == "CARRIER":
        if old_status == "DRAFT" and new_status == "PENDING":
            # Submitting draft is allowed
            pass
        elif new_status == "CANCELLED":
            # Cancelling own appointment is allowed
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Carriers can only submit drafts or cancel their appointments.",
            )

    elif current_user.role in (
        "WAREHOUSE_MANAGER",
        "WAREHOUSE_STAFF",
    ):
        if new_status not in (
            "CONFIRMED",
            "REJECTED",
            "CANCELLED",
            "CHECKED_IN",
            "ARRIVED",
            "IN_PROGRESS",
            "COMPLETED",
            "NO_SHOW",
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot perform this status transition.",
            )

    elif current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to change appointment status.",
        )

    # If assigning dock during confirmation or transition
    target_dock_id = status_data.dock_id if status_data.dock_id is not None else appointment.dock_id

    if new_status == AppointmentStatus.CONFIRMED.value:
        if target_dock_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A dock must be assigned before confirmation.",
            )

    if target_dock_id is not None and (
        new_status in BLOCKING_STATUSES or status_data.dock_id is not None
    ):
        validate_dock_assignment(
            db=db,
            dock_id=target_dock_id,
            warehouse_id=appointment.warehouse_id,
            start_time=appointment.scheduled_start,
            end_time=appointment.scheduled_end,
            exclude_appointment_id=appointment.id,
            cargo_weight_kg=appointment.cargo_weight_kg,
        )
        appointment.dock_id = target_dock_id

    appointment.status = new_status

    if new_status == AppointmentStatus.REJECTED.value:
        appointment.rejection_reason = status_data.reason

    appointment.updated_at = datetime.now(timezone.utc)

    event = AppointmentEvent(
        appointment_id=appointment.id,
        changed_by=current_user.id,
        previous_status=old_status,
        new_status=new_status,
        event_type="STATUS_CHANGED",
        reason=status_data.reason,
    )

    try:
        db.add(event)

        log_audit(
            db=db,
            user_id=current_user.id,
            action=f"STATUS_TRANSITION_{new_status}",
            entity_type="Appointment",
            entity_id=appointment.id,
            description=f"Status transitioned from {old_status} to {new_status} for {appointment.reference_number}. Reason: {status_data.reason or 'None'}",
            old_values={"status": old_status},
            new_values={"status": new_status, "dock_id": appointment.dock_id, "reason": status_data.reason},
        )

        db.commit()
        db.refresh(appointment)

    except Exception:
        db.rollback()
        raise

    return to_response_dto(db, appointment)
