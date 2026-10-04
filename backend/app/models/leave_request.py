from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import HalfDayType, LeaveStatus

if TYPE_CHECKING:
    from app.models.leave_type import LeaveType
    from app.models.user import User
    from app.models.leave_request_allocation import LeaveRequestAllocation


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    __table_args__ = (
        # Date validation
        CheckConstraint(
            "end_date >= start_date",
            name="ck_leave_request_dates_valid",
        ),
        CheckConstraint(
            "total_days > 0",
            name="ck_leave_request_total_days_positive",
        ),

        # Prevent self-approval
        CheckConstraint(
            "approved_by_id IS NULL OR approved_by_id <> user_id",
            name="ck_leave_request_cannot_approve_own_leave",
        ),

        # Performance indexes
        Index(
            "ix_leave_requests_user_status",
            "user_id",
            "status",
        ),
        Index(
            "ix_leave_requests_dates",
            "start_date",
            "end_date",
        ),
        Index(
            "ix_leave_requests_approver_status",
            "approved_by_id",
            "status",
        ),
        Index(
            "ix_leave_requests_leave_type_status",
            "leave_type_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # Employee who requested the leave
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    # Leave type being requested
    leave_type_id: Mapped[int] = mapped_column(
        ForeignKey(
            "leave_types.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Half-day handling
    start_half_day: Mapped[HalfDayType] = mapped_column(
        Enum(
            HalfDayType,
            name="half_day_type_enum",
        ),
        nullable=False,
        default=HalfDayType.NONE,
        server_default=text("'NONE'"),
    )

    end_half_day: Mapped[HalfDayType] = mapped_column(
        Enum(
            HalfDayType,
            name="half_day_type_enum",
        ),
        nullable=False,
        default=HalfDayType.NONE,
        server_default=text("'NONE'"),
    )

    # Calculated working-day quantity
    total_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[LeaveStatus] = mapped_column(
        Enum(
            LeaveStatus,
            name="leave_status_enum",
        ),
        nullable=False,
        default=LeaveStatus.PENDING,
        server_default=text("'PENDING'"),
    )

    # Approval information
    approved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    approval_comment: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Cancellation information
    cancelled_by_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    allocations: Mapped[list["LeaveRequestAllocation"]] = relationship(
        "LeaveRequestAllocation",
        back_populates="leave_request",
        cascade="all, delete-orphan",
        order_by="LeaveRequestAllocation.year",
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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

    # Relationships

    employee: Mapped["User"] = relationship(
        "User",
        back_populates="leave_requests",
        foreign_keys=[user_id],
    )

    @property
    def user(self) -> "User | None":
        return self.employee

    leave_type: Mapped["LeaveType"] = relationship(
        "LeaveType",
        back_populates="leave_requests",
    )

    approver: Mapped["User | None"] = relationship(
        "User",
        back_populates="approved_requests",
        foreign_keys=[approved_by_id],
    )

    canceller: Mapped["User | None"] = relationship(
        "User",
        back_populates="cancelled_requests",
        foreign_keys=[cancelled_by_id],
    )