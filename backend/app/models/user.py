from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import Role

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.leave_balance import LeaveBalance
    from app.models.leave_request import LeaveRequest


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "manager_id IS NULL OR manager_id <> id",
            name="ck_users_manager_not_self",
        ),
        Index(
            "ix_users_manager_id",
            "manager_id",
        ),
        Index(
            "ix_users_role",
            "role",
        ),
    )

    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # User details
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Login identity
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    # Never store plain-text passwords
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Explicitly required role
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role_enum"),
        nullable=False,
    )

    # Employee -> Manager
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    # Account state
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # Login protection
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Login/session tracking
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    password_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Used to invalidate existing JWT sessions
    token_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    # Timestamps
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

    # ---------------------------------------------------------
    # Relationships
    # ---------------------------------------------------------

    # Employee -> Manager
    manager: Mapped["User | None"] = relationship(
        "User",
        back_populates="employees",
        remote_side=[id],
        foreign_keys=[manager_id],
    )

    # Manager -> Employees
    employees: Mapped[list["User"]] = relationship(
        "User",
        back_populates="manager",
        foreign_keys=[manager_id],
    )

    # Employee -> Leave Balances
    leave_balances: Mapped[list["LeaveBalance"]] = relationship(
        "LeaveBalance",
        back_populates="user",
    )

    # Employee -> Leave Requests
    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="employee",
        foreign_keys="LeaveRequest.user_id",
    )

    # Manager/Admin -> Approved Requests
    approved_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="approver",
        foreign_keys="LeaveRequest.approved_by_id",
    )

    # User -> Cancelled Requests
    cancelled_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="canceller",
        foreign_keys="LeaveRequest.cancelled_by_id",
    )

    # User -> Audit Logs
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
        foreign_keys="AuditLog.user_id",
    )