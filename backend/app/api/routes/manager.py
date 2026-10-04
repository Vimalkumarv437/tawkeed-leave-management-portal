from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.enums import LeaveStatus, Role
from app.core.exceptions import (
    AuthorizationError,
    LeaveApprovalError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.permissions import require_role
from app.models.user import User
from app.schemas.leave_request import (
    LeaveDecisionRequest,
    LeaveRequestListResponse,
    LeaveRequestResponse,
)
from app.services.leave_service import LeaveService


router = APIRouter(
    prefix="/manager",
    tags=["Manager"],
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def _handle_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AuthorizationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=exc.message,
        )

    if isinstance(exc, ResourceNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=exc.message,
        )

    if isinstance(
        exc,
        (
            LeaveApprovalError,
            ResourceConflictError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# -------------------------------------------------------------------
# Team requests
# -------------------------------------------------------------------


@router.get(
    "/requests",
    response_model=LeaveRequestListResponse,
    status_code=status.HTTP_200_OK,
)
def get_team_requests(
    status_filter: LeaveStatus | None = Query(
        default=None,
        alias="status",
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        require_role(Role.MANAGER),
    ),
    db: Session = Depends(get_db),
) -> LeaveRequestListResponse:
    """
    Return leave requests belonging only to the current manager's team.
    """

    service = LeaveService(db)

    try:
        items, total = service.list_team_requests(
            manager_id=current_user.id,
            offset=offset,
            limit=limit,
            status=status_filter,
        )

        return LeaveRequestListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    except Exception as exc:
        raise _handle_service_error(exc) from exc


# -------------------------------------------------------------------
# Approve request
# -------------------------------------------------------------------


@router.post(
    "/requests/{request_id}/approve",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_200_OK,
)
def approve_request(
    request_id: int,
    decision: LeaveDecisionRequest,
    current_user: User = Depends(
        require_role(Role.MANAGER),
    ),
    db: Session = Depends(get_db),
) -> LeaveRequestResponse:
    """
    Approve a pending leave request belonging to the manager's team.
    """

    service = LeaveService(db)

    try:
        request = service.approve_leave_request(
            manager_id=current_user.id,
            request_id=request_id,
            comment=decision.comment,
        )

        db.commit()
        db.refresh(request)

        return request

    except Exception as exc:
        db.rollback()
        raise _handle_service_error(exc) from exc


# -------------------------------------------------------------------
# Reject request
# -------------------------------------------------------------------


@router.post(
    "/requests/{request_id}/reject",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_200_OK,
)
def reject_request(
    request_id: int,
    decision: LeaveDecisionRequest,
    current_user: User = Depends(
        require_role(Role.MANAGER),
    ),
    db: Session = Depends(get_db),
) -> LeaveRequestResponse:
    """
    Reject a pending leave request belonging to the manager's team.
    """

    service = LeaveService(db)

    try:
        request = service.reject_leave_request(
            manager_id=current_user.id,
            request_id=request_id,
            comment=decision.comment,
        )

        db.commit()
        db.refresh(request)

        return request

    except Exception as exc:
        db.rollback()
        raise _handle_service_error(exc) from exc


# -------------------------------------------------------------------
# Team calendar
# -------------------------------------------------------------------


@router.get(
    "/calendar",
    response_model=LeaveRequestListResponse,
    status_code=status.HTTP_200_OK,
)
def get_team_calendar(
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(
        require_role(Role.MANAGER),
    ),
    db: Session = Depends(get_db),
) -> LeaveRequestListResponse:
    """
    Return approved leave requests for the current manager's team.

    The frontend can use the returned start_date/end_date values
    to render the calendar.
    """

    service = LeaveService(db)

    try:
        items, total = service.list_team_requests(
            manager_id=current_user.id,
            offset=offset,
            limit=limit,
            status=LeaveStatus.APPROVED,
        )

        return LeaveRequestListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    except Exception as exc:
        raise _handle_service_error(exc) from exc