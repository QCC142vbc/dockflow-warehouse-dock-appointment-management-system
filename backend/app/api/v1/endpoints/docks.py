from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.dock import Dock
from app.models.dock_capability import DockCapability
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser
from app.schemas.dock import (
    DockCreate,
    DockUpdate,
    DockResponse,
)
from app.schemas.dock_capability import (
    DockCapabilityCreate,
    DockCapabilityUpdate,
    DockCapabilityResponse,
)
from app.services.audit import log_audit
from app.services.scheduling_engine import find_available_docks


router = APIRouter()


@router.get(
    "/availability",
    response_model=list[DockResponse],
)
def get_dock_availability(
    warehouse_id: int = Query(...),
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    vehicle_length: float | None = Query(default=None),
    vehicle_weight: float | None = Query(default=None),
    required_capabilities: list[str] | None = Query(default=None),
    exclude_appointment_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        available_docks = find_available_docks(
            db=db,
            warehouse_id=warehouse_id,
            start_time=start_time,
            end_time=end_time,
            vehicle_length=vehicle_length,
            vehicle_weight=vehicle_weight,
            required_capabilities=required_capabilities,
            exclude_appointment_id=exclude_appointment_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return available_docks


@router.get(
    "/",
    response_model=list[DockResponse],
)
def get_docks(
    warehouse_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Dock).order_by(Dock.warehouse_id, Dock.dock_code)

    if current_user.role == "CARRIER":
        # Carriers only see active docks for a warehouse
        statement = statement.where(Dock.is_active.is_(True))
        if warehouse_id is not None:
            statement = statement.where(Dock.warehouse_id == warehouse_id)
    elif current_user.role in ("WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
        assigned = list(
            db.scalars(
                select(WarehouseUser.warehouse_id).where(WarehouseUser.user_id == current_user.id)
            ).all()
        )
        if assigned:
            statement = statement.where(Dock.warehouse_id.in_(assigned))
        if warehouse_id is not None:
            statement = statement.where(Dock.warehouse_id == warehouse_id)
    elif current_user.role == "ADMIN":
        if warehouse_id is not None:
            statement = statement.where(Dock.warehouse_id == warehouse_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view docks.",
        )

    return db.scalars(statement).all()


@router.get(
    "/{dock_id}",
    response_model=DockResponse,
)
def get_dock(
    dock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dock = db.get(Dock, dock_id)

    if dock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock not found.",
        )

    return dock


@router.post(
    "/",
    response_model=DockResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dock(
    dock_data: DockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "WAREHOUSE_MANAGER")),
):
    warehouse = db.get(Warehouse, dock_data.warehouse_id)

    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found.",
        )

    new_dock = Dock(
        **dock_data.model_dump()
    )

    db.add(new_dock)
    db.flush()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_DOCK",
        entity_type="Dock",
        entity_id=new_dock.id,
        description=f"Created dock {new_dock.name} ({new_dock.dock_code}) for warehouse {warehouse.code}",
        new_values=dock_data.model_dump(),
    )

    db.commit()
    db.refresh(new_dock)

    return new_dock


@router.patch(
    "/{dock_id}",
    response_model=DockResponse,
)
def update_dock(
    dock_id: int,
    dock_data: DockUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "WAREHOUSE_MANAGER")),
):
    dock = db.get(Dock, dock_id)

    if dock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock not found.",
        )

    update_data = dock_data.model_dump(exclude_unset=True)
    old_values = {k: getattr(dock, k) for k in update_data.keys()}

    for field, value in update_data.items():
        setattr(dock, field, value)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE_DOCK",
        entity_type="Dock",
        entity_id=dock.id,
        description=f"Updated dock {dock.name} ({dock.dock_code})",
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(dock)

    return dock


@router.get(
    "/{dock_id}/capabilities",
    response_model=list[DockCapabilityResponse],
)
def get_dock_capabilities(
    dock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dock = db.get(Dock, dock_id)

    if dock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock not found.",
        )

    statement = (
        select(DockCapability)
        .where(
            DockCapability.dock_id == dock_id,
            DockCapability.is_active.is_(True),
        )
        .order_by(DockCapability.capability_type)
    )

    return db.scalars(statement).all()


@router.post(
    "/{dock_id}/capabilities",
    response_model=DockCapabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_dock_capability(
    dock_id: int,
    capability_data: DockCapabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "WAREHOUSE_MANAGER")),
):
    dock = db.get(Dock, dock_id)

    if dock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock not found.",
        )

    if capability_data.dock_id != dock_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dock ID in the request body does not match the URL.",
        )

    new_capability = DockCapability(
        **capability_data.model_dump()
    )

    db.add(new_capability)
    db.flush()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_DOCK_CAPABILITY",
        entity_type="DockCapability",
        entity_id=new_capability.id,
        description=f"Created capability {new_capability.capability_type}={new_capability.capability_value} for dock {dock.dock_code}",
        new_values=capability_data.model_dump(),
    )

    db.commit()
    db.refresh(new_capability)

    return new_capability


@router.patch(
    "/capabilities/{capability_id}",
    response_model=DockCapabilityResponse,
)
def update_dock_capability(
    capability_id: int,
    capability_data: DockCapabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN", "WAREHOUSE_MANAGER")),
):
    capability = db.get(DockCapability, capability_id)

    if capability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock capability not found.",
        )

    update_data = capability_data.model_dump(exclude_unset=True)
    old_values = {k: getattr(capability, k) for k in update_data.keys()}

    for field, value in update_data.items():
        setattr(capability, field, value)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE_DOCK_CAPABILITY",
        entity_type="DockCapability",
        entity_id=capability.id,
        description=f"Updated capability {capability.capability_type} on dock {capability.dock_id}",
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(capability)

    return capability