from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CarrierBase(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    registration_number: str = Field(min_length=2, max_length=100)
    contact_email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=300)
    country: str = Field(min_length=2, max_length=100)


class CarrierCreate(CarrierBase):
    pass


class CarrierUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=2, max_length=200)
    registration_number: str | None = Field(default=None, min_length=2, max_length=100)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=300)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    is_active: bool | None = None


class CarrierResponse(CarrierBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)