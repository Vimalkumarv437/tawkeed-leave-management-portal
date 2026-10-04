from datetime import datetime, timezone

from app.core.enums import AuditAction
from app.schemas.audit_log import AuditLogResponse


def test_audit_log_response():
    log = AuditLogResponse(
        id=1,
        user_id=2,
        action=AuditAction.APPROVE_LEAVE,
        entity_type="leave_request",
        entity_id=10,
        details={"comment": "Approved"},
        ip_address="127.0.0.1",
        user_agent="pytest",
        created_at=datetime.now(timezone.utc),
    )

    assert log.id == 1
    assert log.user_id == 2
    assert log.action == AuditAction.APPROVE_LEAVE
    assert log.entity_type == "leave_request"
    assert log.entity_id == 10
    assert log.details["comment"] == "Approved"