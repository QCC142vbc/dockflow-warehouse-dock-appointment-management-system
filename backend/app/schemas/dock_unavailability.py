from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DockUnavailabilityBase(BaseModel):
    dock_id: int = Field(gt=0)
    reason_type: str = Field(min_length=2, max_length=50)
    description: str | None = None

    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_period(self):
        if self.end_time <= self.start_time:
            raise ValueError("Unavailability end must be after start.")

        if self.start_time.tzinfo is None or self.end_time.tzinfo is None:
            raise ValueError("Unavailability timestamps must include timezone information.")

        return self


class DockUnavailabilityCreate(DockUnavailabilityBase):
    reported_by: int | None = Field(default=None, gt=0)


class DockUnavailabilityUpdate(BaseModel):
    reason_type: str | None = Field(default=None, min_length=2, max_length=50)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                raise ValueError("Unavailability end must be after start.")

        for field_name in ("start_time", "end_time"):
            value = getattr(self, field_name)

            if value is not None and value.tzinfo is None:
                raise ValueError(f"{field_name} must include timezone information.")

        return self


class DockUnavailabilityResponse(DockUnavailabilityBase):
    id: int
    reported_by: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)