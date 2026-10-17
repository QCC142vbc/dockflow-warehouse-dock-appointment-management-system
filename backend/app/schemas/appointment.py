from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AppointmentStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    CHECKED_IN = "CHECKED_IN"
    ARRIVED = "ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"


class AppointmentBase(BaseModel):
    warehouse_id: int = Field(gt=0)
    dock_id: int | None = Field(default=None, gt=0)

    scheduled_start: datetime
    scheduled_end: datetime

    vehicle_registration: str = Field(min_length=2, max_length=30)
    vehicle_type: str = Field(min_length=2, max_length=50)

    cargo_type: str = Field(min_length=2, max_length=100)
    cargo_description: str | None = None
    cargo_weight_kg: float | None = Field(default=None, gt=0)

    container_number: str | None = Field(default=None, max_length=30)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.scheduled_end <= self.scheduled_start:
            raise ValueError("Appointment end must be after appointment start.")

        if self.scheduled_start.tzinfo is None or self.scheduled_end.tzinfo is None:
            raise ValueError("Appointment timestamps must include timezone information.")

        return self


class AppointmentCreate(AppointmentBase):
    carrier_id: int = Field(gt=0)
    status: AppointmentStatus = Field(default=AppointmentStatus.PENDING)


class AppointmentUpdate(BaseModel):
    dock_id: int | None = Field(default=None, gt=0)
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None

    vehicle_registration: str | None = Field(default=None, min_length=2, max_length=30)
    vehicle_type: str | None = Field(default=None, min_length=2, max_length=50)

    cargo_type: str | None = Field(default=None, min_length=2, max_length=100)
    cargo_description: str | None = None
    cargo_weight_kg: float | None = Field(default=None, gt=0)

    container_number: str | None = Field(default=None, max_length=30)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.scheduled_start is not None and self.scheduled_end is not None:
            if self.scheduled_end <= self.scheduled_start:
                raise ValueError("Appointment end must be after appointment start.")

        for field_name in ("scheduled_start", "scheduled_end"):
            value = getattr(self, field_name)

            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must include timezone information.")

        return self


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus
    reason: str | None = Field(default=None, max_length=1000)
    dock_id: int | None = Field(default=None, gt=0)


class AppointmentResponse(AppointmentBase):
    id: int
    reference_number: str
    carrier_id: int
    created_by: int
    status: AppointmentStatus
    rejection_reason: str | None
    created_at: datetime
    updated_at: datetime
    carrier_name: str | None = None
    warehouse_name: str | None = None
    dock_code: str | None = None

    model_config = ConfigDict(from_attributes=True)