from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


SENSITIVE_FIELDS = {"password", "hashed_password", "token", "access_token", "secret"}


def sanitize_dict(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data:
        return None
    sanitized = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, datetime):
            sanitized[key] = value.isoformat()
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        else:
            sanitized[key] = value
    return sanitized


def log_audit(
    db: Session,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    description: str | None = None,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """
    Record an audit trail event.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        old_values=sanitize_dict(old_values),
        new_values=sanitize_dict(new_values),
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    # Note: caller will commit or flush as part of their transaction
    return entry
