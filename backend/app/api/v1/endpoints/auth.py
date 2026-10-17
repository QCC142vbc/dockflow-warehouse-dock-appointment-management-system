from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import (
    verify_password,
    create_access_token,
)
from app.models.carrier import Carrier
from app.models.carrier_user import CarrierUser
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def get_user_context(db: Session, user: User) -> dict:
    carrier_info = None
    warehouse_info = []

    if user.role == "CARRIER":
        cu = db.scalar(
            select(CarrierUser).where(CarrierUser.user_id == user.id)
        )
        if cu:
            carrier = db.get(Carrier, cu.carrier_id)
            if carrier:
                carrier_info = {
                    "id": carrier.id,
                    "company_name": carrier.company_name,
                    "registration_number": carrier.registration_number,
                }
    elif user.role in ("WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
        wh_users = list(
            db.scalars(
                select(WarehouseUser).where(WarehouseUser.user_id == user.id)
            ).all()
        )
        for wh_u in wh_users:
            wh = db.get(Warehouse, wh_u.warehouse_id)
            if wh:
                warehouse_info.append({
                    "id": wh.id,
                    "name": wh.name,
                    "code": wh.code,
                })

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "carrier": carrier_info,
        "warehouses": warehouse_info,
    }


@router.post("/login")
@limiter.limit("20/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.scalar(
        select(User).where(
            User.email == form_data.username
        )
    )

    if user is None or not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )

    access_token = create_access_token(
        subject=str(user.id)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": get_user_context(db, user),
    }


@router.get("/me")
def get_current_user_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_context(db, current_user)
