from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DockBase(BaseModel):
    warehouse_id: int = Field(gt=0)
    dock_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=2, max_length=150)
    description: str | None = None
    max_vehicle_length: float | None = Field(default=None, gt=0)
    max_vehicle_weight: float | None = Field(default=None, gt=0)


class DockCreate(DockBase):
    pass


class DockUpdate(BaseModel):
    dock_code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    max_vehicle_length: float | None = Field(default=None, gt=0)
    max_vehicle_weight: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class DockResponse(DockBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)