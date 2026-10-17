from datetime import date
from pydantic import BaseModel, Field


class DailyVolumeItem(BaseModel):
    date: str
    count: int


class DashboardMetrics(BaseModel):
    total_appointments: int = 0
    pending_appointments: int = 0
    confirmed_appointments: int = 0
    completed_appointments: int = 0
    cancelled_appointments: int = 0
    no_show_appointments: int = 0
    in_progress_appointments: int = 0
    checked_in_appointments: int = 0
    dock_utilization_percent: float = Field(default=0.0, ge=0.0, le=100.0)
    status_distribution: dict[str, int] = {}
    daily_volume: list[DailyVolumeItem] = []
    total_docks: int = 0
    active_docks: int = 0
    total_warehouses: int = 0
