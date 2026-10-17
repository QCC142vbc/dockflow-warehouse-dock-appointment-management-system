from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogBase(BaseModel):
    action: str = Field(min_length=2, max_length=100)
    entity_type: str = Field(min_length=2, max_length=100)
    entity_id: int | None = Field(default=None, gt=0)
    description: str | None = None

    old_values: dict[str, Any] | None = None
    new_values: dict[str, Any] | None = None

    ip_address: str | None = Field(default=None, max_length=45)


class AuditLogCreate(AuditLogBase):
    user_id: int | None = Field(default=None, gt=0)


class AuditLogResponse(AuditLogBase):
    id: int
    user_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)