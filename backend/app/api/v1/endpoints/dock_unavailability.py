from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.dock import Dock
from app.models.dock_unavailability import DockUnavailability
from app.models.user import User
from app.schemas.dock_unavailability import (
    DockUnavailabilityCreate,
    DockUnavailabilityUpdate,
    DockUnavailabilityResponse,
)
from app.services.audit import log_audit


router = APIRouter()


@router.get(
    "/",
    response_model=list[DockUnavailabilityResponse],
)
def get_dock_unavailability(
    dock_id: int | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "WAREHOUSE_MANAGER", "WAREHOUSE_STAFF")
    ),
):
    statement = select(DockUnavailability)

    if dock_id is not None:
        statement = statement.where(
            DockUnavailability.dock_id == dock_id
        )

    if start_date is not None:
        statement = statement.where(
            DockUnavailability.end_time > start_date
        )

    if end_date is not None:
        statement = statement.where(
            DockUnavailability.start_time < end_date
        )

    statement = statement.order_by(
        DockUnavailability.start_time
    )

    return db.scalars(statement).all()


@router.get(
    "/{unavailability_id}",
    response_model=DockUnavailabilityResponse,
)
def get_unavailability(
    unavailability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "WAREHOUSE_MANAGER", "WAREHOUSE_STAFF")
    ),
):
    unavailability = db.get(
        DockUnavailability,
        unavailability_id,
    )

    if unavailability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock unavailability record not found.",
        )

    return unavailability


@router.post(
    "/",
    response_model=DockUnavailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_unavailability(
    unavailability_data: DockUnavailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "WAREHOUSE_MANAGER")
    ),
):
    dock = db.get(
        Dock,
        unavailability_data.dock_id,
    )

    if dock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock not found.",
        )

    new_unavailability = DockUnavailability(
        dock_id=unavailability_data.dock_id,
        reason_type=unavailability_data.reason_type,
        description=unavailability_data.description,
        start_time=unavailability_data.start_time,
        end_time=unavailability_data.end_time,
        reported_by=current_user.id,
    )

    db.add(new_unavailability)
    db.flush()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_DOCK_UNAVAILABILITY",
        entity_type="DockUnavailability",
        entity_id=new_unavailability.id,
        description=f"Created {new_unavailability.reason_type} for dock {dock.dock_code}",
        new_values=unavailability_data.model_dump(),
    )

    db.commit()
    db.refresh(new_unavailability)

    return new_unavailability


@router.patch(
    "/{unavailability_id}",
    response_model=DockUnavailabilityResponse,
)
def update_unavailability(
    unavailability_id: int,
    unavailability_data: DockUnavailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "WAREHOUSE_MANAGER")
    ),
):
    unavailability = db.get(
        DockUnavailability,
        unavailability_id,
    )

    if unavailability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock unavailability record not found.",
        )

    update_data = unavailability_data.model_dump(
        exclude_unset=True
    )

    new_start = update_data.get(
        "start_time",
        unavailability.start_time,
    )

    new_end = update_data.get(
        "end_time",
        unavailability.end_time,
    )

    if new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unavailability end must be after start.",
        )

    old_values = {k: getattr(unavailability, k) for k in update_data.keys()}

    for field, value in update_data.items():
        setattr(unavailability, field, value)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE_DOCK_UNAVAILABILITY",
        entity_type="DockUnavailability",
        entity_id=unavailability.id,
        description=f"Updated unavailability {unavailability.id} on dock {unavailability.dock_id}",
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(unavailability)

    return unavailability


@router.delete(
    "/{unavailability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_unavailability(
    unavailability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "WAREHOUSE_MANAGER")
    ),
):
    unavailability = db.get(
        DockUnavailability,
        unavailability_id,
    )

    if unavailability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dock unavailability record not found.",
        )

    log_audit(
        db=db,
        user_id=current_user.id,
        action="DELETE_DOCK_UNAVAILABILITY",
        entity_type="DockUnavailability",
        entity_id=unavailability.id,
        description=f"Deleted unavailability {unavailability.id} ({unavailability.reason_type})",
    )

    db.delete(unavailability)
    db.commit()

    return None