from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.leave_type import LeaveType
    from app.models.user import User


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    __table_args__ = (
        # One balance per employee + leave type + year
        UniqueConstraint(
            "user_id",
            "leave_type_id",
            "year",
            name="uq_leave_balance_user_type_year",
        ),

        # Balance integrity
        CheckConstraint(
            "allocated_days >= 0",
            name="ck_leave_balance_allocated_non_negative",
        ),
        CheckConstraint(
            "used_days >= 0",
            name="ck_leave_balance_used_non_negative",
        ),
        CheckConstraint(
            "reserved_days >= 0",
            name="ck_leave_balance_reserved_non_negative",
        ),
        CheckConstraint(
            "used_days + reserved_days <= allocated_days",
            name="ck_leave_balance_total_usage_valid",
        ),
        CheckConstraint(
            "year >= 2000 AND year <= 2100",
            name="ck_leave_balance_year_valid",
        ),

        Index(
            "ix_leave_balances_user_year",
            "user_id",
            "year",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey(
            "leave_types.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    allocated_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        server_default=text("0.00"),
    )

    used_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )

    # Pending leave reservations
    reserved_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default=text("0.00"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="leave_balances",
    )

    leave_type: Mapped["LeaveType"] = relationship(
        "LeaveType",
        back_populates="leave_balances",
    )

    @property
    def remaining_days(self) -> Decimal:
        """
        Remaining available balance.

        Reserved pending leave is excluded from the available amount.
        """
        return (
            self.allocated_days
            - self.used_days
            - self.reserved_days
        )