from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.enums import AuditAction, HalfDayType, LeaveStatus, Role
from app.core.exceptions import (
    AuthorizationError,
    InsufficientBalanceError,
    InvalidLeaveDateError,
    LeaveApprovalError,
    LeaveCancellationError,
    OverlappingLeaveError,
)
from app.models.audit_log import AuditLog
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.user import User
from app.services.leave_service import LeaveService
from app.services.working_days import calculate_working_days


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def create_user(
    db,
    *,
    role: Role,
    manager_id: int | None = None,
) -> User:
    user = User(
        first_name="Test",
        last_name=role.value.title(),
        email=f"{unique_value('user')}@example.com",
        password_hash="test-password-hash",
        role=role,
        manager_id=manager_id,
        is_active=True,
    )

    db.add(user)
    db.flush()

    return user


def create_manager(db) -> User:
    return create_user(
        db,
        role=Role.MANAGER,
    )


def create_employee(
    db,
    *,
    manager: User,
) -> User:
    return create_user(
        db,
        role=Role.EMPLOYEE,
        manager_id=manager.id,
    )


def create_leave_type(
    db,
    *,
    allowance: Decimal = Decimal("20.00"),
) -> LeaveType:
    leave_type = LeaveType(
        name=unique_value("Annual Leave"),
        code=unique_value("TEST").upper(),
        description="Test leave type",
        default_annual_allowance=allowance,
        is_active=True,
    )

    db.add(leave_type)
    db.flush()

    return leave_type


def create_balance(
    db,
    *,
    employee: User,
    leave_type: LeaveType,
    year: int,
    allocated: Decimal = Decimal("20.00"),
    used: Decimal = Decimal("0.00"),
    reserved: Decimal = Decimal("0.00"),
) -> LeaveBalance:
    balance = LeaveBalance(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=year,
        allocated_days=allocated,
        used_days=used,
        reserved_days=reserved,
    )

    db.add(balance)
    db.flush()

    return balance


def next_weekday(days_ahead: int = 7) -> date:
    """
    Return a deterministic future Monday-Friday date.
    """
    result = date.today() + timedelta(days=days_ahead)

    while result.weekday() >= 5:
        result += timedelta(days=1)

    return result


def next_saturday(days_ahead: int = 7) -> date:
    result = date.today() + timedelta(days=days_ahead)

    while result.weekday() != 5:
        result += timedelta(days=1)

    return result


def future_weekday_after(days_ahead: int = 14) -> date:
    return next_weekday(days_ahead)


def create_employee_setup(db, *, balance_days: Decimal = Decimal("20.00")):
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )
    leave_type = create_leave_type(db)

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=date.today().year,
        allocated=balance_days,
    )

    return manager, employee, leave_type


# -------------------------------------------------------------------
# Create leave request
# -------------------------------------------------------------------


def test_employee_can_create_valid_leave_request(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()
    end = start

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=end,
        reason="Personal work",
    )

    assert request.id is not None
    assert request.user_id == employee.id
    assert request.leave_type_id == leave_type.id
    assert request.start_date == start
    assert request.end_date == end
    assert request.total_days == Decimal("1.00")
    assert request.status == LeaveStatus.PENDING
    assert request.reason == "Personal work"

    assert len(request.allocations) == 1
    assert request.allocations[0].year == start.year
    assert request.allocations[0].allocated_days == Decimal("1.00")


def test_leave_request_reserves_balance(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("10.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.allocated_days == Decimal("10.00")
    assert balance.used_days == Decimal("0.00")
    assert balance.reserved_days == Decimal("1.00")
    assert balance.remaining_days == Decimal("9.00")


def test_leave_cannot_start_in_the_past(db):
    manager, employee, leave_type = create_employee_setup(db)

    past_date = date.today() - timedelta(days=1)
    while past_date.weekday() >= 5:
        past_date -= timedelta(days=1)

    service = LeaveService(db)

    with pytest.raises(
        InvalidLeaveDateError,
        match="Leave cannot start in the past.",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=past_date,
            end_date=past_date,
        )


def test_end_date_before_start_date_is_rejected(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()
    end = start - timedelta(days=1)

    service = LeaveService(db)

    with pytest.raises(
        InvalidLeaveDateError,
        match="End date cannot be before start date.",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=start,
            end_date=end,
        )


def test_weekend_only_leave_is_rejected(db):
    manager, employee, leave_type = create_employee_setup(db)

    weekend = next_saturday()

    service = LeaveService(db)

    with pytest.raises(
        InvalidLeaveDateError,
        match="Leave request must contain at least one working day.",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=weekend,
            end_date=weekend,
        )


def test_public_holiday_only_leave_is_rejected(db):
    manager, employee, leave_type = create_employee_setup(db)

    holiday_date = future_weekday_after()

    from app.models.public_holiday import PublicHoliday

    holiday = PublicHoliday(
        holiday_date=holiday_date,
        name="Test Holiday",
        description="Testing holiday exclusion",
    )

    db.add(holiday)
    db.flush()

    service = LeaveService(db)

    with pytest.raises(
        InvalidLeaveDateError,
        match="Leave request must contain at least one working day.",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=holiday_date,
            end_date=holiday_date,
        )


def test_insufficient_balance_is_rejected(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("1.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    with pytest.raises(
        InsufficientBalanceError,
        match="Insufficient leave balance",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=start,
            end_date=start + timedelta(days=1),
        )


def test_exact_remaining_balance_is_accepted(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("2.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start + timedelta(days=1),
    )

    assert request.total_days == Decimal("2.00")

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.reserved_days == Decimal("2.00")
    assert balance.remaining_days == Decimal("0.00")


def test_single_day_half_day_leave_is_calculated_correctly(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("5.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
        start_half_day=HalfDayType.FIRST_HALF,
        end_half_day=HalfDayType.NONE,
    )

    assert request.total_days == Decimal("0.50")
    assert request.allocations[0].allocated_days == Decimal("0.50")


def test_invalid_single_day_half_day_configuration_is_rejected(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("5.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    with pytest.raises(
        ValueError,
        match="For single-day leave, only one half-day",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=start,
            end_date=start,
            start_half_day=HalfDayType.FIRST_HALF,
            end_half_day=HalfDayType.SECOND_HALF,
        )


# -------------------------------------------------------------------
# Overlap rules
# -------------------------------------------------------------------


def test_pending_leave_overlap_is_rejected(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start + timedelta(days=2),
    )

    with pytest.raises(
        OverlappingLeaveError,
        match="overlaps an existing pending or approved leave request",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=start + timedelta(days=1),
            end_date=start + timedelta(days=3),
        )


def test_approved_leave_overlap_is_rejected(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.approve_leave_request(
        manager_id=manager.id,
        request_id=request.id,
        comment="Approved",
    )

    with pytest.raises(
        OverlappingLeaveError,
        match="overlaps an existing pending or approved leave request",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=start,
            end_date=start,
        )


def test_rejected_leave_does_not_block_new_leave(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.reject_leave_request(
        manager_id=manager.id,
        request_id=request.id,
        comment="Not approved",
    )

    new_request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    assert new_request.status == LeaveStatus.PENDING


def test_cancelled_leave_does_not_block_new_leave(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.cancel_leave_request(
        employee_id=employee.id,
        request_id=request.id,
        reason="Plans changed",
    )

    new_request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    assert new_request.status == LeaveStatus.PENDING


def test_adjacent_non_overlapping_leave_is_allowed(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("10.00"),
    )

    first_start = next_weekday()
    first_end = first_start

    second_start = first_start + timedelta(days=2)

    while second_start.weekday() >= 5:
        second_start += timedelta(days=1)

    service = LeaveService(db)

    first = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=first_start,
        end_date=first_end,
    )

    service.cancel_leave_request(
        employee_id=employee.id,
        request_id=first.id,
    )

    second = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=second_start,
        end_date=second_start,
    )

    assert second.status == LeaveStatus.PENDING


# -------------------------------------------------------------------
# Approval
# -------------------------------------------------------------------


def test_manager_can_approve_own_team_leave(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    result = service.approve_leave_request(
        manager_id=manager.id,
        request_id=request.id,
        comment="Approved for personal work.",
    )

    assert result.status == LeaveStatus.APPROVED
    assert result.approved_by_id == manager.id
    assert result.approval_comment == "Approved for personal work."
    assert result.approved_at is not None


def test_approval_moves_reserved_balance_to_used(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("10.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    assert employee.leave_balances is not None

    service.approve_leave_request(
        manager_id=manager.id,
        request_id=request.id,
    )

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.reserved_days == Decimal("0.00")
    assert balance.used_days == Decimal("1.00")
    assert balance.remaining_days == Decimal("9.00")


def test_already_approved_leave_cannot_be_approved_again(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.approve_leave_request(
        manager_id=manager.id,
        request_id=request.id,
    )

    with pytest.raises(
        LeaveApprovalError,
        match="Only pending leave requests can be approved",
    ):
        service.approve_leave_request(
            manager_id=manager.id,
            request_id=request.id,
        )


def test_manager_cannot_approve_another_team_leave(db):
    manager1 = create_manager(db)
    manager2 = create_manager(db)

    employee2 = create_employee(
        db,
        manager=manager2,
    )

    leave_type = create_leave_type(db)

    start = next_weekday()

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type,
        year=start.year,
    )

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee2.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    with pytest.raises(
        AuthorizationError,
        match="your own team",
    ):
        service.approve_leave_request(
            manager_id=manager1.id,
            request_id=request.id,
        )


def test_manager_cannot_approve_own_leave(db):
    manager = create_manager(db)
    leave_type = create_leave_type(db)

    start = next_weekday()

    create_balance(
        db,
        employee=manager,
        leave_type=leave_type,
        year=start.year,
        allocated=Decimal("10.00"),
    )

    # Create a manager leave request directly for this service-level
    # authorization test.
    from app.models.leave_request import LeaveRequest
    from app.models.leave_request_allocation import LeaveRequestAllocation

    request = LeaveRequest(
        user_id=manager.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
        start_half_day=HalfDayType.NONE,
        end_half_day=HalfDayType.NONE,
        total_days=Decimal("1.00"),
        reason="Manager leave",
        status=LeaveStatus.PENDING,
    )

    db.add(request)
    db.flush()

    db.add(
        LeaveRequestAllocation(
            leave_request_id=request.id,
            year=start.year,
            allocated_days=Decimal("1.00"),
        )
    )

    db.flush()

    service = LeaveService(db)

    with pytest.raises(
        AuthorizationError,
        match="cannot approve or reject their own leave",
    ):
        service.approve_leave_request(
            manager_id=manager.id,
            request_id=request.id,
        )


# -------------------------------------------------------------------
# Rejection
# -------------------------------------------------------------------


def test_manager_can_reject_own_team_leave(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    result = service.reject_leave_request(
        manager_id=manager.id,
        request_id=request.id,
        comment="Business requirement.",
    )

    assert result.status == LeaveStatus.REJECTED
    assert result.approval_comment == "Business requirement."


def test_rejection_releases_reserved_balance(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("10.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.reject_leave_request(
        manager_id=manager.id,
        request_id=request.id,
    )

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.reserved_days == Decimal("0.00")
    assert balance.used_days == Decimal("0.00")
    assert balance.remaining_days == Decimal("10.00")


def test_rejected_leave_cannot_be_approved(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.reject_leave_request(
        manager_id=manager.id,
        request_id=request.id,
    )

    with pytest.raises(
        LeaveApprovalError,
        match="Only pending leave requests can be approved",
    ):
        service.approve_leave_request(
            manager_id=manager.id,
            request_id=request.id,
        )


def test_manager_cannot_reject_another_team_leave(db):
    manager1 = create_manager(db)
    manager2 = create_manager(db)
    employee2 = create_employee(db, manager=manager2)

    leave_type = create_leave_type(db)

    start = next_weekday()

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type,
        year=start.year,
    )

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee2.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    with pytest.raises(
        AuthorizationError,
        match="your own team",
    ):
        service.reject_leave_request(
            manager_id=manager1.id,
            request_id=request.id,
        )


# -------------------------------------------------------------------
# Cancellation
# -------------------------------------------------------------------


def test_employee_can_cancel_pending_leave(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("10.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    result = service.cancel_leave_request(
        employee_id=employee.id,
        request_id=request.id,
        reason="Plans changed.",
    )

    assert result.status == LeaveStatus.CANCELLED
    assert result.cancelled_by_id == employee.id
    assert result.cancellation_reason == "Plans changed."
    assert result.cancelled_at is not None


def test_pending_cancellation_releases_reserved_balance(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("10.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.cancel_leave_request(
        employee_id=employee.id,
        request_id=request.id,
    )

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.reserved_days == Decimal("0.00")
    assert balance.used_days == Decimal("0.00")
    assert balance.remaining_days == Decimal("10.00")


def test_approved_leave_can_be_cancelled(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("10.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.approve_leave_request(
        manager_id=manager.id,
        request_id=request.id,
    )

    result = service.cancel_leave_request(
        employee_id=employee.id,
        request_id=request.id,
        reason="No longer needed.",
    )

    assert result.status == LeaveStatus.CANCELLED
    assert result.cancelled_by_id == employee.id


def test_approved_cancellation_restores_used_balance(db):
    manager, employee, leave_type = create_employee_setup(
        db,
        balance_days=Decimal("10.00"),
    )

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.approve_leave_request(
        manager_id=manager.id,
        request_id=request.id,
    )

    service.cancel_leave_request(
        employee_id=employee.id,
        request_id=request.id,
        reason="Cancelled.",
    )

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.used_days == Decimal("0.00")
    assert balance.reserved_days == Decimal("0.00")
    assert balance.remaining_days == Decimal("10.00")


def test_employee_cannot_cancel_another_employee_leave(db):
    manager = create_manager(db)
    employee1 = create_employee(db, manager=manager)
    employee2 = create_employee(db, manager=manager)

    leave_type = create_leave_type(db)
    start = next_weekday()

    create_balance(
        db,
        employee=employee1,
        leave_type=leave_type,
        year=start.year,
    )

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type,
        year=start.year,
    )

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee1.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    with pytest.raises(
        AuthorizationError,
        match="only cancel your own",
    ):
        service.cancel_leave_request(
            employee_id=employee2.id,
            request_id=request.id,
        )


def test_rejected_leave_cannot_be_cancelled(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.reject_leave_request(
        manager_id=manager.id,
        request_id=request.id,
    )

    with pytest.raises(
        LeaveCancellationError,
        match="Only pending or approved leave can be cancelled",
    ):
        service.cancel_leave_request(
            employee_id=employee.id,
            request_id=request.id,
        )


def test_cancelled_leave_cannot_be_cancelled_again(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.cancel_leave_request(
        employee_id=employee.id,
        request_id=request.id,
    )

    with pytest.raises(
        LeaveCancellationError,
        match="Only pending or approved leave can be cancelled",
    ):
        service.cancel_leave_request(
            employee_id=employee.id,
            request_id=request.id,
        )


# -------------------------------------------------------------------
# Year-spanning leave
# -------------------------------------------------------------------


def test_year_spanning_leave_creates_two_allocations(db):
    manager = create_manager(db)
    employee = create_employee(db, manager=manager)
    leave_type = create_leave_type(db)

    start_year = date.today().year + 1

    start = date(start_year, 12, 30)
    end = date(start_year + 1, 1, 5)

    first_year_days = calculate_working_days(
        start_date=start,
        end_date=date(start_year, 12, 31),
    )

    second_year_days = calculate_working_days(
        start_date=date(start_year + 1, 1, 1),
        end_date=end,
    )

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=start_year,
        allocated=first_year_days,
    )

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=start_year + 1,
        allocated=second_year_days,
    )

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=end,
    )

    assert len(request.allocations) == 2

    allocations = {
        allocation.year: allocation.allocated_days
        for allocation in request.allocations
    }

    assert allocations[start_year] == first_year_days
    assert allocations[start_year + 1] == second_year_days

    assert request.total_days == (
        first_year_days + second_year_days
    )


def test_year_spanning_leave_reserves_each_year_balance(db):
    manager = create_manager(db)
    employee = create_employee(db, manager=manager)
    leave_type = create_leave_type(db)

    start_year = date.today().year + 1

    start = date(start_year, 12, 30)
    end = date(start_year + 1, 1, 5)

    first_year_days = calculate_working_days(
        start_date=start,
        end_date=date(start_year, 12, 31),
    )

    second_year_days = calculate_working_days(
        start_date=date(start_year + 1, 1, 1),
        end_date=end,
    )

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=start_year,
        allocated=first_year_days,
    )

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=start_year + 1,
        allocated=second_year_days,
    )

    service = LeaveService(db)

    service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=end,
    )

    balance1 = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start_year,
        )
    )

    balance2 = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start_year + 1,
        )
    )

    assert balance1 is not None
    assert balance2 is not None

    assert balance1.reserved_days == first_year_days
    assert balance2.reserved_days == second_year_days


def test_year_spanning_leave_rejects_when_second_year_balance_is_insufficient(
    db,
):
    manager = create_manager(db)
    employee = create_employee(db, manager=manager)
    leave_type = create_leave_type(db)

    start_year = date.today().year + 1

    start = date(start_year, 12, 30)
    end = date(start_year + 1, 1, 5)

    first_year_days = calculate_working_days(
        start_date=start,
        end_date=date(start_year, 12, 31),
    )

    second_year_days = calculate_working_days(
        start_date=date(start_year + 1, 1, 1),
        end_date=end,
    )

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=start_year,
        allocated=first_year_days,
    )

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=start_year + 1,
        allocated=Decimal("0.00"),
    )

    service = LeaveService(db)

    with pytest.raises(
        InsufficientBalanceError,
        match="Insufficient leave balance",
    ):
        service.create_leave_request(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            start_date=start,
            end_date=end,
        )

    balance1 = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start_year,
        )
    )

    balance2 = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start_year + 1,
        )
    )

    assert balance1 is not None
    assert balance2 is not None

    # Validation happens before reservation, so neither year is changed.
    assert balance1.reserved_days == Decimal("0.00")
    assert balance2.reserved_days == Decimal("0.00")


# -------------------------------------------------------------------
# Audit records
# -------------------------------------------------------------------


def test_create_leave_creates_audit_record(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "leave_request",
            AuditLog.entity_id == request.id,
            AuditLog.action == AuditAction.CREATE_LEAVE,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.user_id == employee.id
    assert audit.details is not None
    assert audit.details["total_days"] == "1.00"


def test_approval_creates_audit_record(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.approve_leave_request(
        manager_id=manager.id,
        request_id=request.id,
        comment="Approved.",
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "leave_request",
            AuditLog.entity_id == request.id,
            AuditLog.action == AuditAction.APPROVE_LEAVE,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.user_id == manager.id


def test_rejection_creates_audit_record(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.reject_leave_request(
        manager_id=manager.id,
        request_id=request.id,
        comment="Rejected.",
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "leave_request",
            AuditLog.entity_id == request.id,
            AuditLog.action == AuditAction.REJECT_LEAVE,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.user_id == manager.id


def test_cancellation_creates_audit_record(db):
    manager, employee, leave_type = create_employee_setup(db)

    start = next_weekday()

    service = LeaveService(db)

    request = service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
    )

    service.cancel_leave_request(
        employee_id=employee.id,
        request_id=request.id,
        reason="Cancelled by employee.",
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "leave_request",
            AuditLog.entity_id == request.id,
            AuditLog.action == AuditAction.CANCEL_LEAVE,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.user_id == employee.id
    assert audit.details is not None
    assert audit.details["previous_status"] == "PENDING"