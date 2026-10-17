from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AppointmentEventBase(BaseModel):
    appointment_id: int = Field(gt=0)
    previous_status: str | None = Field(default=None, max_length=30)
    new_status: str = Field(min_length=2, max_length=30)
    reason: str | None = None
    event_type: str = Field(min_length=2, max_length=50)


class AppointmentEventCreate(AppointmentEventBase):
    changed_by: int | None = Field(default=None, gt=0)


class AppointmentEventResponse(AppointmentEventBase):
    id: int
    changed_by: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)