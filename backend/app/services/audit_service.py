from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.enums import AuditAction
from app.models.audit_log import AuditLog


class AuditService:
    """
    Handles creation of application audit records.

    Audit records are append-only from the application
    perspective. They provide a history of important
    actions performed by users.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def log(
        self,
        *,
        user_id: int | None,
        action: AuditAction,
        entity_type: str,
        entity_id: int,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """
        Create an audit record.

        The caller controls the transaction. This means the
        audit record can be committed together with the
        business operation it describes.
        """

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)

        return audit_log