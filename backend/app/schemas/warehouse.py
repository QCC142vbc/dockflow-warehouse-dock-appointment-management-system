from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WarehouseBase(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    code: str = Field(min_length=2, max_length=50)
    address: str = Field(min_length=2, max_length=300)
    city: str = Field(min_length=2, max_length=100)
    postal_code: str = Field(min_length=2, max_length=20)
    country: str = Field(min_length=2, max_length=100)
    timezone: str = Field(default="Europe/Budapest", max_length=100)


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    code: str | None = Field(default=None, min_length=2, max_length=50)
    address: str | None = Field(default=None, min_length=2, max_length=300)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    postal_code: str | None = Field(default=None, min_length=2, max_length=20)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    timezone: str | None = Field(default=None, max_length=100)
    is_active: bool | None = None


class WarehouseResponse(WarehouseBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)