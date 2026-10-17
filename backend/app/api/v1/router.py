from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    carriers,
    warehouses,
    docks,
    appointments,
    dock_unavailability,
    dashboard,
    audit_logs,
)


api_router = APIRouter()


api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
)

api_router.include_router(
    carriers.router,
    prefix="/carriers",
    tags=["Carriers"],
)

api_router.include_router(
    warehouses.router,
    prefix="/warehouses",
    tags=["Warehouses"],
)

api_router.include_router(
    docks.router,
    prefix="/docks",
    tags=["Docks"],
)

api_router.include_router(
    appointments.router,
    prefix="/appointments",
    tags=["Appointments"],
)

api_router.include_router(
    dock_unavailability.router,
    prefix="/dock-unavailability",
    tags=["Dock Unavailability"],
)

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
)

api_router.include_router(
    audit_logs.router,
    prefix="/audit-logs",
    tags=["Audit Logs"],
)