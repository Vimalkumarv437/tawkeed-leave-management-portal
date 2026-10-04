from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import AuditAction, Role
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.permissions import require_role
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import AuditLogListResponse


router = APIRouter(
    prefix="/admin/audit-logs",
    tags=["Audit"],
)


# -------------------------------------------------------------------
# Admin audit log
# -------------------------------------------------------------------


@router.get(
    "",
    response_model=AuditLogListResponse,
)
def list_audit_logs(
    offset: int = Query(
        0,
        ge=0,
        description="Number of records to skip",
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of records to return",
    ),
    action: AuditAction | None = Query(
        None,
        description="Filter by audit action",
    ),
    user_id: int | None = Query(
        None,
        ge=1,
        description="Filter by actor user ID",
    ),
    entity_type: str | None = Query(
        None,
        min_length=1,
        max_length=100,
        description="Filter by entity type",
    ),
    entity_id: int | None = Query(
        None,
        ge=1,
        description="Filter by entity ID",
    ),
    current_user: User = Depends(
        require_role(Role.ADMIN)
    ),
    db: Session = Depends(get_db),
):
    """
    Return audit log entries for administrators.

    Results are ordered from newest to oldest.
    """

    filters = []

    if action is not None:
        filters.append(AuditLog.action == action)

    if user_id is not None:
        filters.append(AuditLog.user_id == user_id)

    if entity_type is not None:
        filters.append(
            AuditLog.entity_type == entity_type.strip()
        )

    if entity_id is not None:
        filters.append(AuditLog.entity_id == entity_id)

    # ---------------------------------------------------------------
    # Total count
    # ---------------------------------------------------------------

    count_stmt = select(
        func.count(AuditLog.id)
    )

    if filters:
        count_stmt = count_stmt.where(*filters)

    total = db.scalar(count_stmt) or 0

    # ---------------------------------------------------------------
    # Audit log records
    # ---------------------------------------------------------------

    stmt = (
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .where(*filters)
        .order_by(
            AuditLog.created_at.desc(),
            AuditLog.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    items = list(
        db.scalars(stmt).all()
    )

    return AuditLogListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )