from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_yms_service_auth
from app.models.appointment import Appointment
from app.models.carrier import Carrier
from app.models.dock import Dock
from app.models.warehouse import Warehouse
from app.services.external_refs import external_reference

router = APIRouter(dependencies=[Depends(require_yms_service_auth)])


@router.get("/appointments/{appointment_id}")
def get_appointment_reference(
    appointment_id: str,
    db: Session = Depends(get_db),
):
    appointment = db.scalar(
        select(Appointment).where(Appointment.appointment_id == appointment_id)
    )
    if appointment is None:
        appointment = db.scalar(
            select(Appointment).where(
                func.upper(Appointment.reference_number) == appointment_id.strip().upper()
            )
        )
    if appointment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found.")
    warehouse = db.get(Warehouse, appointment.warehouse_id)
    carrier = db.get(Carrier, appointment.carrier_id)
    dock = db.get(Dock, appointment.dock_id) if appointment.dock_id else None
    if warehouse is None or carrier is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Appointment references are incomplete in Scheduling.",
        )
    return {
        "appointment_id": appointment.appointment_id,
        "reference_number": appointment.reference_number,
        "status": appointment.status,
        "scheduled_start": appointment.scheduled_start,
        "scheduled_end": appointment.scheduled_end,
        "vehicle_registration": appointment.vehicle_registration,
        "vehicle_type": appointment.vehicle_type,
        "carrier_name": carrier.company_name,
        "external_carrier_id": external_reference(carrier, "carrier"),
        "external_warehouse_id": external_reference(warehouse, "warehouse"),
        "external_dock_id": external_reference(dock, "dock") if dock else None,
    }


@router.get("/warehouses")
def get_warehouse_references(db: Session = Depends(get_db)):
    warehouses = db.scalars(
        select(Warehouse).where(Warehouse.is_active.is_(True)).order_by(Warehouse.name)
    ).all()
    return [
        {
            "external_warehouse_id": external_reference(warehouse, "warehouse"),
            "name": warehouse.name,
            "code": warehouse.code,
            "timezone": warehouse.timezone,
            "is_active": warehouse.is_active,
        }
        for warehouse in warehouses
    ]


@router.get("/warehouses/{external_warehouse_id}/docks")
def get_dock_references(
    external_warehouse_id: str,
    db: Session = Depends(get_db),
):
    warehouses = db.scalars(select(Warehouse)).all()
    warehouse = next(
        (
            item
            for item in warehouses
            if external_reference(item, "warehouse") == external_warehouse_id
        ),
        None,
    )
    if warehouse is None or not warehouse.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
    docks = db.scalars(
        select(Dock)
        .where(Dock.warehouse_id == warehouse.id, Dock.is_active.is_(True))
        .order_by(Dock.dock_code)
    ).all()
    return [
        {
            "external_dock_id": external_reference(dock, "dock"),
            "external_warehouse_id": external_reference(warehouse, "warehouse"),
            "dock_code": dock.dock_code,
            "name": dock.name,
            "is_active": dock.is_active,
        }
        for dock in docks
    ]


@router.get("/carriers/{external_carrier_id}")
def get_carrier_reference(
    external_carrier_id: str,
    db: Session = Depends(get_db),
):
    carriers = db.scalars(select(Carrier)).all()
    carrier = next(
        (item for item in carriers if external_reference(item, "carrier") == external_carrier_id),
        None,
    )
    if carrier is None or not carrier.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Carrier not found.")
    return {
        "external_carrier_id": external_reference(carrier, "carrier"),
        "company_name": carrier.company_name,
        "registration_number": carrier.registration_number,
        "is_active": carrier.is_active,
    }
