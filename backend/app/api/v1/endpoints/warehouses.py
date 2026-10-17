from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser
from app.schemas.warehouse import (
    WarehouseCreate,
    WarehouseUpdate,
    WarehouseResponse,
)
from app.services.audit import log_audit


router = APIRouter()


@router.get(
    "/",
    response_model=list[WarehouseResponse],
)
def get_warehouses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Warehouse).order_by(Warehouse.name)

    if current_user.role == "CARRIER":
        statement = statement.where(Warehouse.is_active.is_(True))
    elif current_user.role in ("WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
        assigned = list(
            db.scalars(
                select(WarehouseUser.warehouse_id).where(WarehouseUser.user_id == current_user.id)
            ).all()
        )
        if assigned:
            statement = statement.where(Warehouse.id.in_(assigned))
    elif current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view warehouses.",
        )

    return db.scalars(statement).all()


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
)
def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    warehouse = db.get(Warehouse, warehouse_id)

    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found.",
        )

    if current_user.role in ("WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
        assigned = list(
            db.scalars(
                select(WarehouseUser.warehouse_id).where(WarehouseUser.user_id == current_user.id)
            ).all()
        )
        if assigned and warehouse_id not in assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this warehouse.",
            )

    return warehouse


@router.post(
    "/",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_warehouse(
    warehouse_data: WarehouseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    existing_warehouse = db.scalar(
        select(Warehouse).where(
            Warehouse.code == warehouse_data.code
        )
    )

    if existing_warehouse:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A warehouse with this code already exists.",
        )

    new_warehouse = Warehouse(
        **warehouse_data.model_dump()
    )

    db.add(new_warehouse)
    db.flush()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_WAREHOUSE",
        entity_type="Warehouse",
        entity_id=new_warehouse.id,
        description=f"Created warehouse {new_warehouse.name} ({new_warehouse.code})",
        new_values=warehouse_data.model_dump(),
    )

    db.commit()
    db.refresh(new_warehouse)

    return new_warehouse


@router.patch(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
)
def update_warehouse(
    warehouse_id: int,
    warehouse_data: WarehouseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    warehouse = db.get(Warehouse, warehouse_id)

    if warehouse is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Warehouse not found.",
        )

    update_data = warehouse_data.model_dump(exclude_unset=True)

    if "code" in update_data and update_data["code"] is not None:
        existing_warehouse = db.scalar(
            select(Warehouse).where(
                Warehouse.code == update_data["code"],
                Warehouse.id != warehouse_id,
            )
        )

        if existing_warehouse:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This warehouse code is already in use.",
            )

    old_values = {k: getattr(warehouse, k) for k in update_data.keys()}
    for field, value in update_data.items():
        setattr(warehouse, field, value)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE_WAREHOUSE",
        entity_type="Warehouse",
        entity_id=warehouse.id,
        description=f"Updated warehouse {warehouse.name} ({warehouse.code})",
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(warehouse)

    return warehouse