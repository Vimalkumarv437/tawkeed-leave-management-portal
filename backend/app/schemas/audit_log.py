from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import AuditAction


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: AuditAction
    entity_type: str
    entity_id: int | None
    details: dict[str, Any] | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)