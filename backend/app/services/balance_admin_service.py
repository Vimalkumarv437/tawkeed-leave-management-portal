from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import Role
from app.core.exceptions import (
    InsufficientBalanceError,
    InvalidManagerError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.user import User
from app.schemas.leave_balance import (
    LeaveBalanceCreate,
    LeaveBalanceUpdate,
)


class BalanceAdminService:
    """
    Handles administrator management of yearly leave allowances.

    Only allocated_days is managed here.

    used_days and reserved_days are controlled exclusively by
    the leave workflow.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_employee(
        self,
        user_id: int,
    ) -> User:
        user = self.db.get(User, user_id)

        if user is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        if user.role != Role.EMPLOYEE:
            raise InvalidManagerError(
                "Leave balance can only be assigned to employees."
            )

        return user

    def _get_leave_type(
        self,
        leave_type_id: int,
    ) -> LeaveType:
        leave_type = self.db.get(
            LeaveType,
            leave_type_id,
        )

        if leave_type is None:
            raise ResourceNotFoundError(
                "Leave type not found."
            )

        return leave_type

    def _get_balance(
        self,
        *,
        balance_id: int,
    ) -> LeaveBalance:
        balance = self.db.get(
            LeaveBalance,
            balance_id,
        )

        if balance is None:
            raise ResourceNotFoundError(
                "Leave balance not found."
            )

        return balance

    # ------------------------------------------------------------------
    # Get
    # ------------------------------------------------------------------

    def get_balance(
        self,
        *,
        balance_id: int,
    ) -> LeaveBalance:
        return self._get_balance(
            balance_id=balance_id,
        )

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_balances(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        year: int | None = None,
        user_id: int | None = None,
        leave_type_id: int | None = None,
    ) -> tuple[list[LeaveBalance], int]:
        if offset < 0:
            raise ValueError(
                "Offset cannot be negative."
            )

        if limit < 1 or limit > 100:
            raise ValueError(
                "Limit must be between 1 and 100."
            )

        filters: list[Any] = []

        if year is not None:
            filters.append(
                LeaveBalance.year == year
            )

        if user_id is not None:
            filters.append(
                LeaveBalance.user_id == user_id
            )

        if leave_type_id is not None:
            filters.append(
                LeaveBalance.leave_type_id == leave_type_id
            )

        total = self.db.scalar(
            select(func.count(LeaveBalance.id)).where(*filters)
        ) or 0

        balances = list(
            self.db.scalars(
                select(LeaveBalance)
                .where(*filters)
                .order_by(
                    LeaveBalance.year,
                    LeaveBalance.user_id,
                    LeaveBalance.leave_type_id,
                )
                .offset(offset)
                .limit(limit)
            ).all()
        )

        return balances, total

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_balance(
        self,
        *,
        data: LeaveBalanceCreate,
    ) -> LeaveBalance:
        self._get_employee(
            data.user_id,
        )

        self._get_leave_type(
            data.leave_type_id,
        )

        existing = self.db.scalar(
            select(LeaveBalance).where(
                LeaveBalance.user_id == data.user_id,
                LeaveBalance.leave_type_id == data.leave_type_id,
                LeaveBalance.year == data.year,
            )
        )

        if existing is not None:
            raise ResourceConflictError(
                "A leave balance already exists for this "
                "employee, leave type and year."
            )

        balance = LeaveBalance(
            user_id=data.user_id,
            leave_type_id=data.leave_type_id,
            year=data.year,
            allocated_days=Decimal(
                data.allocated_days
            ),
            used_days=Decimal("0.00"),
            reserved_days=Decimal("0.00"),
        )

        self.db.add(balance)

        try:
            self.db.flush()
        except IntegrityError as exc:
            raise ResourceConflictError(
                "A leave balance already exists for this "
                "employee, leave type and year."
            ) from exc

        return balance

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_balance(
        self,
        *,
        balance_id: int,
        data: LeaveBalanceUpdate,
    ) -> LeaveBalance:
        balance = self._get_balance(
            balance_id=balance_id,
        )

        new_allocated = Decimal(
            data.allocated_days
        )

        committed_days = (
            balance.used_days
            + balance.reserved_days
        )

        if new_allocated < committed_days:
            raise InsufficientBalanceError(
                "Allocated days cannot be less than "
                "used plus reserved days."
            )

        balance.allocated_days = new_allocated

        self.db.flush()

        return balance