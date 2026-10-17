from datetime import datetime, timedelta, timezone
from collections import defaultdict
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.appointment import Appointment
from app.models.carrier_user import CarrierUser
from app.models.dock import Dock
from app.models.user import User
from app.models.warehouse import Warehouse
from app.models.warehouse_user import WarehouseUser
from app.schemas.dashboard import DashboardMetrics, DailyVolumeItem
from app.services.scheduling_engine import BLOCKING_STATUSES, normalize_datetime

router = APIRouter()


@router.get("/metrics", response_model=DashboardMetrics)
def get_dashboard_metrics(
    warehouse_id: int | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    start_period = now - timedelta(days=days)
    end_period = now + timedelta(days=days)

    # Scoping
    carrier_ids: list[int] = []
    warehouse_ids: list[int] = []

    if current_user.role == "CARRIER":
        carrier_ids = list(
            db.scalars(
                select(CarrierUser.carrier_id).where(CarrierUser.user_id == current_user.id)
            ).all()
        )
    elif current_user.role in ("WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"):
        assigned = list(
            db.scalars(
                select(WarehouseUser.warehouse_id).where(WarehouseUser.user_id == current_user.id)
            ).all()
        )
        if assigned:
            warehouse_ids = assigned
        elif warehouse_id:
            warehouse_ids = [warehouse_id]

    if warehouse_id is not None and current_user.role == "ADMIN":
        warehouse_ids = [warehouse_id]

    # Appointment base query
    appt_query = select(Appointment)
    if carrier_ids:
        appt_query = appt_query.where(Appointment.carrier_id.in_(carrier_ids))
    if warehouse_ids:
        appt_query = appt_query.where(Appointment.warehouse_id.in_(warehouse_ids))

    appointments = db.scalars(appt_query).all()

    # Docks query
    dock_query = select(Dock)
    if warehouse_ids:
        dock_query = dock_query.where(Dock.warehouse_id.in_(warehouse_ids))
    docks = db.scalars(dock_query).all()
    total_docks = len(docks)
    active_docks = sum(1 for d in docks if d.is_active)

    # Warehouse count
    wh_query = select(func.count(Warehouse.id)).where(Warehouse.is_active.is_(True))
    if warehouse_ids:
        wh_query = wh_query.where(Warehouse.id.in_(warehouse_ids))
    total_warehouses = db.scalar(wh_query) or 0

    # Aggregate status counts
    status_counts: dict[str, int] = defaultdict(int)
    for appt in appointments:
        status_counts[appt.status] += 1

    # Daily volume calculation
    daily_counts: dict[str, int] = defaultdict(int)
    # Generate past days + upcoming days keys for continuous series
    cur_day = (now - timedelta(days=days)).date()
    end_day = (now + timedelta(days=1)).date()
    while cur_day <= end_day:
        daily_counts[cur_day.isoformat()] = 0
        cur_day += timedelta(days=1)

    for appt in appointments:
        if appt.scheduled_start:
            dt = normalize_datetime(appt.scheduled_start).date().isoformat()
            if dt in daily_counts:
                daily_counts[dt] += 1

    daily_volume = [
        DailyVolumeItem(date=d, count=c)
        for d, c in sorted(daily_counts.items())
    ]

    # Dock utilization calculation (blocking appointments in next/past days vs dock capacity)
    # Total hours booked by blocking appointments
    total_booked_hours = 0.0
    for appt in appointments:
        if appt.status in BLOCKING_STATUSES:
            s = normalize_datetime(appt.scheduled_start)
            e = normalize_datetime(appt.scheduled_end)
            if s >= start_period and e <= end_period:
                duration_hours = max(0.0, (e - s).total_seconds() / 3600.0)
                total_booked_hours += duration_hours

    # Standard operational hours: 12 hours per day per active dock
    operational_hours_available = max(1.0, active_docks * days * 2 * 12.0)
    utilization = round(min(100.0, (total_booked_hours / operational_hours_available) * 100.0), 1)

    return DashboardMetrics(
        total_appointments=len(appointments),
        pending_appointments=status_counts["PENDING"],
        confirmed_appointments=status_counts["CONFIRMED"],
        completed_appointments=status_counts["COMPLETED"],
        cancelled_appointments=status_counts["CANCELLED"],
        no_show_appointments=status_counts["NO_SHOW"],
        in_progress_appointments=status_counts["IN_PROGRESS"],
        checked_in_appointments=status_counts["CHECKED_IN"],
        dock_utilization_percent=utilization,
        status_distribution=dict(status_counts),
        daily_volume=daily_volume,
        total_docks=total_docks,
        active_docks=active_docks,
        total_warehouses=total_warehouses,
    )
