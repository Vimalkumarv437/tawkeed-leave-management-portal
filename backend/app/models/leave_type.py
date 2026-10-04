from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.leave_balance import LeaveBalance
    from app.models.leave_request import LeaveRequest


class LeaveType(Base):
    __tablename__ = "leave_types"

    __table_args__ = (
        CheckConstraint(
            "default_annual_allowance >= 0",
            name="ck_leave_types_allowance_non_negative",
        ),
        Index(
            "ix_leave_types_is_active",
            "is_active",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    # User-facing name
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    # Stable business identifier
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Supports full and half-day allowances
    default_annual_allowance: Mapped[Decimal] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        server_default=text("0.00"),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
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

    leave_balances: Mapped[list["LeaveBalance"]] = relationship(
        "LeaveBalance",
        back_populates="leave_type",
    )

    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="leave_type",
    )