from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.leave_request import LeaveRequest


class LeaveRequestAllocation(Base):
    """
    Stores the portion of a leave request belonging to
    each calendar year.

    Example:

        Leave request:
        30-Dec-2026 -> 05-Jan-2027

        2026 -> 2.00 days
        2027 -> 3.00 days
    """

    __tablename__ = "leave_request_allocations"

    __table_args__ = (
        UniqueConstraint(
            "leave_request_id",
            "year",
            name="uq_leave_request_allocation_request_year",
        ),
        CheckConstraint(
            "allocated_days > 0",
            name="ck_leave_request_allocation_days_positive",
        ),
        CheckConstraint(
            "year >= 2000 AND year <= 2100",
            name="ck_leave_request_allocation_year_valid",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    leave_request_id: Mapped[int] = mapped_column(
        ForeignKey(
            "leave_requests.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    year: Mapped[int] = mapped_column(
        nullable=False,
    )

    allocated_days: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    leave_request: Mapped["LeaveRequest"] = relationship(
        "LeaveRequest",
        back_populates="allocations",
    )