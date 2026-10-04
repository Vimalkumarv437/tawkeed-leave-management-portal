from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    InsufficientBalanceError,
    ResourceNotFoundError,
)
from app.models.leave_balance import LeaveBalance


class BalanceService:
    """
    Handles leave balance operations.

    Responsibilities:
    - Read employee balances
    - Reserve balance for pending leave
    - Release reservations
    - Move reserved balance to used balance on approval
    - Restore used balance when approved leave is cancelled

    Transaction management is intentionally left to the
    caller. This allows leave creation, balance changes,
    and audit logging to succeed or fail as one transaction.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ---------------------------------------------------------
    # Read
    # ---------------------------------------------------------

    def get_balance(
        self,
        *,
        user_id: int,
        leave_type_id: int,
        year: int,
    ) -> LeaveBalance:
        """
        Get an employee's balance for a leave type and year.
        """

        balance = self.db.scalar(
            select(LeaveBalance).where(
                LeaveBalance.user_id == user_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year,
            )
        )

        if balance is None:
            raise ResourceNotFoundError(
                "Leave balance not found."
            )

        return balance

    def get_remaining_days(
        self,
        *,
        user_id: int,
        leave_type_id: int,
        year: int,
    ) -> Decimal:
        """
        Return the currently available balance.

        Available balance =
            allocated - used - reserved
        """

        balance = self.get_balance(
            user_id=user_id,
            leave_type_id=leave_type_id,
            year=year,
        )

        return balance.remaining_days

    # ---------------------------------------------------------
    # Internal locked lookup
    # ---------------------------------------------------------

    def _get_balance_for_update(
        self,
        *,
        user_id: int,
        leave_type_id: int,
        year: int,
    ) -> LeaveBalance:
        """
        Retrieve a balance row with a database row lock.

        SELECT ... FOR UPDATE prevents concurrent transactions
        from modifying the same balance simultaneously.
        """

        statement = (
            select(LeaveBalance)
            .where(
                LeaveBalance.user_id == user_id,
                LeaveBalance.leave_type_id == leave_type_id,
                LeaveBalance.year == year,
            )
            .with_for_update()
        )

        balance = self.db.scalar(statement)

        if balance is None:
            raise ResourceNotFoundError(
                "Leave balance not found."
            )

        return balance

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    @staticmethod
    def _validate_days(days: Decimal) -> Decimal:
        """
        Validate a leave quantity.

        Leave is supported in increments of 0.5 day.
        """

        days = Decimal(days)

        if days <= Decimal("0.00"):
            raise ValueError(
                "Leave days must be greater than zero."
            )

        # Only 0.50-day increments are allowed.
        if (days * Decimal("2")) % Decimal("1") != 0:
            raise ValueError(
                "Leave days must be in 0.5-day increments."
            )

        return days

    # ---------------------------------------------------------
    # Reserve balance
    # ---------------------------------------------------------

    def reserve_days(
        self,
        *,
        user_id: int,
        leave_type_id: int,
        year: int,
        days: Decimal,
    ) -> LeaveBalance:
        """
        Reserve balance for a pending leave request.

        Reservation does NOT deduct from used_days.

        Example:
            allocated = 20
            used = 5
            reserved = 0

            reserve 3 days

            allocated = 20
            used = 5
            reserved = 3
            available = 12
        """

        days = self._validate_days(days)

        balance = self._get_balance_for_update(
            user_id=user_id,
            leave_type_id=leave_type_id,
            year=year,
        )

        remaining = balance.remaining_days

        if days > remaining:
            raise InsufficientBalanceError(
                "Insufficient leave balance."
            )

        balance.reserved_days += days

        return balance

    # ---------------------------------------------------------
    # Release reservation
    # ---------------------------------------------------------

    def release_reserved_days(
        self,
        *,
        user_id: int,
        leave_type_id: int,
        year: int,
        days: Decimal,
    ) -> LeaveBalance:
        """
        Release previously reserved days.

        Used when:
        - A pending leave is rejected.
        - A pending leave is cancelled.
        """

        days = self._validate_days(days)

        balance = self._get_balance_for_update(
            user_id=user_id,
            leave_type_id=leave_type_id,
            year=year,
        )

        if balance.reserved_days < days:
            raise ValueError(
                "Reserved balance is insufficient."
            )

        balance.reserved_days -= days

        return balance

    # ---------------------------------------------------------
    # Approve reserved balance
    # ---------------------------------------------------------

    def approve_reserved_days(
        self,
        *,
        user_id: int,
        leave_type_id: int,
        year: int,
        days: Decimal,
    ) -> LeaveBalance:
        """
        Convert reserved days into used days.

        This is performed when a manager approves a pending
        leave request.

        Example:

            Before:
                used = 5
                reserved = 3

            After approval:
                used = 8
                reserved = 0
        """

        days = self._validate_days(days)

        balance = self._get_balance_for_update(
            user_id=user_id,
            leave_type_id=leave_type_id,
            year=year,
        )

        if balance.reserved_days < days:
            raise ValueError(
                "Reserved balance is insufficient."
            )

        balance.reserved_days -= days
        balance.used_days += days

        return balance

    # ---------------------------------------------------------
    # Restore approved balance
    # ---------------------------------------------------------

    def restore_used_days(
        self,
        *,
        user_id: int,
        leave_type_id: int,
        year: int,
        days: Decimal,
    ) -> LeaveBalance:
        """
        Restore previously used days.

        Used when an approved leave request is cancelled.
        """

        days = self._validate_days(days)

        balance = self._get_balance_for_update(
            user_id=user_id,
            leave_type_id=leave_type_id,
            year=year,
        )

        if balance.used_days < days:
            raise ValueError(
                "Used balance is insufficient."
            )

        balance.used_days -= days

        return balance