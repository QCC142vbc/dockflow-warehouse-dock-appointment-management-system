from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DockCapabilityBase(BaseModel):
    dock_id: int = Field(gt=0)
    capability_type: str = Field(min_length=2, max_length=100)
    capability_value: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=300)


class DockCapabilityCreate(DockCapabilityBase):
    pass


class DockCapabilityUpdate(BaseModel):
    capability_type: str | None = Field(default=None, min_length=2, max_length=100)
    capability_value: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=300)
    is_active: bool | None = None


class DockCapabilityResponse(DockCapabilityBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)