from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import Role
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.permissions import require_role
from app.models.leave_balance import LeaveBalance
from app.models.leave_request import LeaveRequest
from app.models.user import User
from app.schemas.leave_balance import LeaveBalanceListResponse
from app.schemas.leave_request import LeaveRequestListResponse


router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


# -------------------------------------------------------------------
# Current employee balances
# -------------------------------------------------------------------


@router.get(
    "/me/balances",
    response_model=LeaveBalanceListResponse,
)
def get_my_balances(
    year: int = Query(
        ...,
        ge=2000,
        le=2100,
        description="Leave balance year",
    ),
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
    current_user: User = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER)
    ),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated employee/manager's leave balances
    for the requested year.
    """

    count_stmt = select(func.count(LeaveBalance.id)).where(
        LeaveBalance.user_id == current_user.id,
        LeaveBalance.year == year,
    )

    total = db.scalar(count_stmt) or 0

    stmt = (
        select(LeaveBalance)
        .where(
            LeaveBalance.user_id == current_user.id,
            LeaveBalance.year == year,
        )
        .order_by(
            LeaveBalance.leave_type_id.asc(),
            LeaveBalance.id.asc(),
        )
        .offset(offset)
        .limit(limit)
    )

    items = list(db.scalars(stmt).all())

    return LeaveBalanceListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        year=year,
    )


# -------------------------------------------------------------------
# Current employee leave history
# -------------------------------------------------------------------


@router.get(
    "/me/leaves",
    response_model=LeaveRequestListResponse,
)
def get_my_leave_history(
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
    current_user: User = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER)
    ),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated employee/manager's leave history.
    """

    count_stmt = select(func.count(LeaveRequest.id)).where(
        LeaveRequest.user_id == current_user.id,
    )

    total = db.scalar(count_stmt) or 0

    stmt = (
        select(LeaveRequest)
        .options(
            selectinload(LeaveRequest.allocations),
        )
        .where(
            LeaveRequest.user_id == current_user.id,
        )
        .order_by(
            LeaveRequest.created_at.desc(),
            LeaveRequest.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    items = list(db.scalars(stmt).all())

    return LeaveRequestListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )