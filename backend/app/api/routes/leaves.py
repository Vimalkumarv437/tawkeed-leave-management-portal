from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.enums import Role
from app.core.exceptions import (
    AuthorizationError,
    InsufficientBalanceError,
    InvalidLeaveDateError,
    LeaveCancellationError,
    OverlappingLeaveError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.dependencies.permissions import require_role
from app.models.user import User
from app.schemas.leave_request import (
    LeaveRequestCreate,
    LeaveRequestDetailResponse,
    LeaveRequestResponse,
)
from app.services.leave_service import LeaveService


router = APIRouter(
    prefix="/leaves",
    tags=["Leaves"],
)


def _service_error(exc: Exception) -> HTTPException:
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
            ResourceConflictError,
            InsufficientBalanceError,
            OverlappingLeaveError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        )

    if isinstance(
        exc,
        (
            InvalidLeaveDateError,
            LeaveCancellationError,
        ),
    ):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# =====================================================================
# Create leave
# =====================================================================


@router.post(
    "",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_leave(
    data: LeaveRequestCreate,
    current_user: User = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER)
    ),
    db: Session = Depends(get_db),
) -> LeaveRequestResponse:
    """
    Create a leave request for the authenticated employee/manager.
    """

    service = LeaveService(db)

    try:
        request = service.create_leave_request(
            employee_id=current_user.id,
            leave_type_id=data.leave_type_id,
            start_date=data.start_date,
            end_date=data.end_date,
            start_half_day=data.start_half_day,
            end_half_day=data.end_half_day,
            reason=data.reason,
        )

        db.commit()
        db.refresh(request)

        return LeaveRequestResponse.model_validate(request)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


# =====================================================================
# Get leave request
# =====================================================================


@router.get(
    "/{request_id}",
    response_model=LeaveRequestDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_leave(
    request_id: int,
    current_user: User = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER)
    ),
    db: Session = Depends(get_db),
) -> LeaveRequestDetailResponse:
    """
    Return a leave request only when it belongs to the current user.
    """

    service = LeaveService(db)

    try:
        request = service.get_request(
            request_id=request_id,
        )

        if request.user_id != current_user.id:
            raise AuthorizationError(
                "You can only view your own leave requests."
            )

        return LeaveRequestDetailResponse.model_validate(request)

    except Exception as exc:
        raise _service_error(exc) from exc


# =====================================================================
# Cancel leave
# =====================================================================


@router.post(
    "/{request_id}/cancel",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_leave(
    request_id: int,
    current_user: User = Depends(
        require_role(Role.EMPLOYEE, Role.MANAGER)
    ),
    db: Session = Depends(get_db),
) -> LeaveRequestResponse:
    """
    Cancel the authenticated user's pending or approved leave.
    """

    service = LeaveService(db)

    try:
        request = service.cancel_leave_request(
            employee_id=current_user.id,
            request_id=request_id,
        )

        db.commit()
        db.refresh(request)

        return LeaveRequestResponse.model_validate(request)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc