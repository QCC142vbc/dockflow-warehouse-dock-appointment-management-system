from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.carrier import Carrier
from app.models.carrier_user import CarrierUser
from app.models.user import User
from app.schemas.carrier import (
    CarrierCreate,
    CarrierUpdate,
    CarrierResponse,
)
from app.services.audit import log_audit


router = APIRouter()


@router.get(
    "/",
    response_model=list[CarrierResponse],
)
def get_carriers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "CARRIER":
        user_carrier_ids = list(
            db.scalars(
                select(CarrierUser.carrier_id).where(
                    CarrierUser.user_id == current_user.id
                )
            ).all()
        )
        statement = select(Carrier).where(Carrier.id.in_(user_carrier_ids)).order_by(Carrier.company_name)
    elif current_user.role in ("ADMIN", "WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
        statement = select(Carrier).order_by(Carrier.company_name)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view carriers.",
        )

    return db.scalars(statement).all()


@router.get(
    "/{carrier_id}",
    response_model=CarrierResponse,
)
def get_carrier(
    carrier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == "CARRIER":
        user_carrier_ids = list(
            db.scalars(
                select(CarrierUser.carrier_id).where(
                    CarrierUser.user_id == current_user.id
                )
            ).all()
        )
        if carrier_id not in user_carrier_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this carrier.",
            )
    elif current_user.role not in ("ADMIN", "WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view carrier details.",
        )

    carrier = db.get(Carrier, carrier_id)

    if carrier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrier not found.",
        )

    return carrier


@router.post(
    "/",
    response_model=CarrierResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_carrier(
    carrier_data: CarrierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    existing_carrier = db.scalar(
        select(Carrier).where(
            Carrier.registration_number == carrier_data.registration_number
        )
    )

    if existing_carrier:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A carrier with this registration number already exists.",
        )

    new_carrier = Carrier(
        **carrier_data.model_dump()
    )

    db.add(new_carrier)
    db.flush()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_CARRIER",
        entity_type="Carrier",
        entity_id=new_carrier.id,
        description=f"Created carrier {new_carrier.company_name}",
        new_values=carrier_data.model_dump(),
    )

    db.commit()
    db.refresh(new_carrier)

    return new_carrier


@router.patch(
    "/{carrier_id}",
    response_model=CarrierResponse,
)
def update_carrier(
    carrier_id: int,
    carrier_data: CarrierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    carrier = db.get(Carrier, carrier_id)

    if carrier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Carrier not found.",
        )

    update_data = carrier_data.model_dump(exclude_unset=True)

    if "registration_number" in update_data:
        registration_number = update_data["registration_number"]

        if registration_number is not None:
            existing_carrier = db.scalar(
                select(Carrier).where(
                    Carrier.registration_number == registration_number,
                    Carrier.id != carrier_id,
                )
            )

            if existing_carrier:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This registration number is already in use.",
                )

    old_values = {k: getattr(carrier, k) for k in update_data.keys()}
    for field, value in update_data.items():
        setattr(carrier, field, value)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE_CARRIER",
        entity_type="Carrier",
        entity_id=carrier.id,
        description=f"Updated carrier {carrier.company_name}",
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(carrier)

    return carrier