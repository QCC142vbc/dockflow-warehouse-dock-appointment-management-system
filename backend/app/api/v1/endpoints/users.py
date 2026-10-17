from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.core.security import hash_password
from app.models.carrier import Carrier
from app.models.carrier_user import CarrierUser
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
)
from app.services.audit import log_audit


router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get(
    "/",
    response_model=list[UserResponse],
)
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    statement = select(User).order_by(User.id)
    return db.scalars(statement).all()


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


@router.get(
    "/{user_id}/assignments",
)
def get_user_assignments(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    carriers = []
    cus = db.scalars(select(CarrierUser).where(CarrierUser.user_id == user_id)).all()
    for cu in cus:
        c = db.get(Carrier, cu.carrier_id)
        if c:
            carriers.append({"id": c.id, "company_name": c.company_name, "registration_number": c.registration_number})

    warehouses = []
    wus = db.scalars(select(WarehouseUser).where(WarehouseUser.user_id == user_id)).all()
    for wu in wus:
        w = db.get(Warehouse, wu.warehouse_id)
        if w:
            warehouses.append({"id": w.id, "name": w.name, "code": w.code})

    return {
        "user_id": user_id,
        "carriers": carriers,
        "warehouses": warehouses,
    }


@router.post(
    "/{user_id}/carrier/{carrier_id}",
    status_code=status.HTTP_201_CREATED,
)
def assign_user_to_carrier(
    user_id: int,
    carrier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    carrier = db.get(Carrier, carrier_id)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found.")

    existing = db.scalar(
        select(CarrierUser).where(CarrierUser.user_id == user_id, CarrierUser.carrier_id == carrier_id)
    )
    if existing:
        return {"message": "Already assigned."}

    cu = CarrierUser(user_id=user_id, carrier_id=carrier_id)
    db.add(cu)
    log_audit(db, current_user.id, "ASSIGN_USER_CARRIER", "User", user_id, f"Assigned user {user.email} to carrier {carrier.company_name}")
    db.commit()
    return {"message": "Carrier assigned successfully."}


@router.delete(
    "/{user_id}/carrier/{carrier_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_user_from_carrier(
    user_id: int,
    carrier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    cu = db.scalar(
        select(CarrierUser).where(CarrierUser.user_id == user_id, CarrierUser.carrier_id == carrier_id)
    )
    if cu:
        db.delete(cu)
        log_audit(db, current_user.id, "UNASSIGN_USER_CARRIER", "User", user_id, f"Unassigned carrier {carrier_id} from user {user_id}")
        db.commit()
    return None


@router.post(
    "/{user_id}/warehouse/{warehouse_id}",
    status_code=status.HTTP_201_CREATED,
)
def assign_user_to_warehouse(
    user_id: int,
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    warehouse = db.get(Warehouse, warehouse_id)
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found.")

    existing = db.scalar(
        select(WarehouseUser).where(WarehouseUser.user_id == user_id, WarehouseUser.warehouse_id == warehouse_id)
    )
    if existing:
        return {"message": "Already assigned."}

    wu = WarehouseUser(user_id=user_id, warehouse_id=warehouse_id)
    db.add(wu)
    log_audit(db, current_user.id, "ASSIGN_USER_WAREHOUSE", "User", user_id, f"Assigned user {user.email} to warehouse {warehouse.name}")
    db.commit()
    return {"message": "Warehouse assigned successfully."}


@router.delete(
    "/{user_id}/warehouse/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unassign_user_from_warehouse(
    user_id: int,
    warehouse_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    wu = db.scalar(
        select(WarehouseUser).where(WarehouseUser.user_id == user_id, WarehouseUser.warehouse_id == warehouse_id)
    )
    if wu:
        db.delete(wu)
        log_audit(db, current_user.id, "UNASSIGN_USER_WAREHOUSE", "User", user_id, f"Unassigned warehouse {warehouse_id} from user {user_id}")
        db.commit()
    return None


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    existing_user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
    )

    db.add(new_user)
    db.flush()

    log_audit(
        db=db,
        user_id=current_user.id,
        action="CREATE_USER",
        entity_type="User",
        entity_id=new_user.id,
        description=f"Created user {new_user.email} with role {new_user.role}",
        new_values={"email": new_user.email, "full_name": new_user.full_name, "role": new_user.role},
    )

    db.commit()
    db.refresh(new_user)

    return new_user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] is not None:
        existing_user = db.scalar(
            select(User).where(
                User.email == update_data["email"],
                User.id != user_id,
            )
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email is already used by another user.",
            )

    old_values = {"email": user.email, "full_name": user.full_name, "is_active": user.is_active}

    if "password" in update_data:
        password = update_data.pop("password")
        if password is not None:
            user.hashed_password = hash_password(password)

    for field, value in update_data.items():
        setattr(user, field, value)

    log_audit(
        db=db,
        user_id=current_user.id,
        action="UPDATE_USER",
        entity_type="User",
        entity_id=user.id,
        description=f"Updated user {user.email}",
        old_values=old_values,
        new_values=update_data,
    )

    db.commit()
    db.refresh(user)

    return user