from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.enums import Role
from app.core.exceptions import (
    AuthorizationError,
    InsufficientBalanceError,
    InvalidManagerError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.dependencies.database import get_db
from app.dependencies.permissions import require_role
from app.models.user import User
from app.schemas.auth import CurrentUserResponse
from app.schemas.leave_balance import (
    LeaveBalanceCreate,
    LeaveBalanceListResponse,
    LeaveBalanceResponse,
    LeaveBalanceUpdate,
)
from app.schemas.leave_type import (
    LeaveTypeCreate,
    LeaveTypeListResponse,
    LeaveTypeResponse,
    LeaveTypeUpdate,
)
from app.schemas.public_holiday import (
    PublicHolidayCreate,
    PublicHolidayListResponse,
    PublicHolidayResponse,
    PublicHolidayUpdate,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.balance_admin_service import BalanceAdminService
from app.services.holiday_service import HolidayService
from app.services.leave_type_service import LeaveTypeService
from app.services.user_service import UserService


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
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

    if isinstance(exc, (ResourceConflictError, InsufficientBalanceError)):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        )

    if isinstance(exc, InvalidManagerError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc),
    )


# =====================================================================
# USERS
# =====================================================================


@router.get(
    "/users",
    response_model=list[CurrentUserResponse],
    status_code=status.HTTP_200_OK,
)
def get_users(
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    role: Role | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> list[CurrentUserResponse]:
    service = UserService(db)

    try:
        users, _ = service.list_users(
            offset=offset,
            limit=limit,
            role=role,
            is_active=is_active,
        )

        return [
            CurrentUserResponse.model_validate(user)
            for user in users
        ]

    except Exception as exc:
        raise _service_error(exc) from exc


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    data: UserCreate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)

    try:
        user = service.create_user(
            data=data,
            actor_user_id=current_user.id,
        )

        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)

    try:
        user = service.update_user(
            user_id=user_id,
            data=data,
            actor_user_id=current_user.id,
        )

        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.delete(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)

    try:
        user = service.deactivate_user(
            user_id=user_id,
            actor_user_id=current_user.id,
        )

        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.post(
    "/users/{user_id}/reactivate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def reactivate_user(
    user_id: int,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)

    try:
        user = service.reactivate_user(
            user_id=user_id,
            actor_user_id=current_user.id,
        )

        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


# =====================================================================
# LEAVE TYPES
# =====================================================================


@router.get(
    "/leave-types",
    response_model=LeaveTypeListResponse,
    status_code=status.HTTP_200_OK,
)
def get_leave_types(
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    is_active: bool | None = Query(default=None),
) -> LeaveTypeListResponse:
    service = LeaveTypeService(db)

    try:
        items, total = service.list_leave_types(
            offset=offset,
            limit=limit,
            is_active=is_active,
        )

        return LeaveTypeListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    except Exception as exc:
        raise _service_error(exc) from exc


@router.post(
    "/leave-types",
    response_model=LeaveTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_leave_type(
    data: LeaveTypeCreate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> LeaveTypeResponse:
    service = LeaveTypeService(db)

    try:
        leave_type = service.create_leave_type(
            data=data,
            actor_user_id=current_user.id,
        )

        db.commit()
        db.refresh(leave_type)

        return LeaveTypeResponse.model_validate(leave_type)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.patch(
    "/leave-types/{leave_type_id}",
    response_model=LeaveTypeResponse,
    status_code=status.HTTP_200_OK,
)
def update_leave_type(
    leave_type_id: int,
    data: LeaveTypeUpdate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> LeaveTypeResponse:
    service = LeaveTypeService(db)

    try:
        leave_type = service.update_leave_type(
            leave_type_id=leave_type_id,
            data=data,
            actor_user_id=current_user.id,
        )

        db.commit()
        db.refresh(leave_type)

        return LeaveTypeResponse.model_validate(leave_type)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


# =====================================================================
# YEARLY BALANCES / ALLOWANCES
# =====================================================================


@router.get(
    "/balances",
    response_model=LeaveBalanceListResponse,
    status_code=status.HTTP_200_OK,
)
def get_balances(
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    year: int | None = Query(default=None, ge=2000, le=2100),
    user_id: int | None = Query(default=None, gt=0),
    leave_type_id: int | None = Query(default=None, gt=0),
) -> LeaveBalanceListResponse:
    service = BalanceAdminService(db)

    try:
        items, total = service.list_balances(
            offset=offset,
            limit=limit,
            year=year,
            user_id=user_id,
            leave_type_id=leave_type_id,
        )

        response_items = [
            LeaveBalanceResponse.model_validate(item)
            for item in items
        ]

        return LeaveBalanceListResponse(
            items=response_items,
            total=total,
            offset=offset,
            limit=limit,
            year=year,
         )

    except Exception as exc:
        raise _service_error(exc) from exc


@router.post(
    "/balances",
    response_model=LeaveBalanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_balance(
    data: LeaveBalanceCreate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> LeaveBalanceResponse:
    service = BalanceAdminService(db)

    try:
        balance = service.create_balance(
            data=data,
        )

        db.commit()
        db.refresh(balance)

        return LeaveBalanceResponse.model_validate(balance)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.patch(
    "/balances/{balance_id}",
    response_model=LeaveBalanceResponse,
    status_code=status.HTTP_200_OK,
)
def update_balance(
    balance_id: int,
    data: LeaveBalanceUpdate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> LeaveBalanceResponse:
    service = BalanceAdminService(db)

    try:
        balance = service.update_balance(
            balance_id=balance_id,
            data=data,
        )

        db.commit()
        db.refresh(balance)

        return LeaveBalanceResponse.model_validate(balance)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc
# =====================================================================
# PUBLIC HOLIDAYS
# =====================================================================

from datetime import date
@router.get(
    "/holidays",
    response_model=PublicHolidayListResponse,
    status_code=status.HTTP_200_OK,
)
def get_holidays(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> PublicHolidayListResponse:
    service = HolidayService(db)

    try:
        items = service.list_holidays(
            start_date=start_date,
            end_date=end_date,
        )

        return PublicHolidayListResponse(
            items=items,
            total=len(items),
            offset=0,
            limit=len(items) if items else 0,
        )

    except Exception as exc:
        raise _service_error(exc) from exc


@router.post(
    "/holidays",
    response_model=PublicHolidayResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_holiday(
    data: PublicHolidayCreate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> PublicHolidayResponse:
    service = HolidayService(db)

    try:
        holiday = service.create_holiday(
            holiday_date=data.holiday_date,
            name=data.name,
            description=data.description,
        )

        return PublicHolidayResponse.model_validate(holiday)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.patch(
    "/holidays/{holiday_id}",
    response_model=PublicHolidayResponse,
    status_code=status.HTTP_200_OK,
)
def update_holiday(
    holiday_id: int,
    data: PublicHolidayUpdate,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> PublicHolidayResponse:
    service = HolidayService(db)

    try:
        holiday = service.update_holiday(
            holiday_id=holiday_id,
            holiday_date=data.holiday_date,
            name=data.name,
            description=data.description,
        )

        return PublicHolidayResponse.model_validate(holiday)

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc


@router.delete(
    "/holidays/{holiday_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_holiday(
    holiday_id: int,
    current_user: User = Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
) -> None:
    service = HolidayService(db)

    try:
        service.delete_holiday(
            holiday_id=holiday_id,
        )

    except Exception as exc:
        db.rollback()
        raise _service_error(exc) from exc