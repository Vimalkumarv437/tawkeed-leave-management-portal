from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.enums import Role
from app.core.exceptions import (
    InsufficientBalanceError,
    InvalidManagerError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import hash_password
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.user import User
from app.schemas.leave_balance import (
    LeaveBalanceCreate,
    LeaveBalanceUpdate,
)
from app.services.balance_admin_service import BalanceAdminService


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def create_user(
    db,
    *,
    role: Role,
    is_active: bool = True,
) -> User:
    user = User(
        first_name="Balance",
        last_name="Admin",
        email=f"{unique_value('user')}@example.com",
        password_hash=hash_password("StrongPassword123!"),
        role=role,
        is_active=is_active,
    )

    db.add(user)
    db.flush()

    return user


def create_leave_type(
    db,
    *,
    allowance: Decimal = Decimal("20.00"),
    is_active: bool = True,
) -> LeaveType:
    leave_type = LeaveType(
        name=unique_value("Leave Type"),
        code=unique_value("CODE").upper(),
        description="Balance admin test leave type",
        default_annual_allowance=allowance,
        is_active=is_active,
    )

    db.add(leave_type)
    db.flush()

    return leave_type


def create_balance(
    db,
    *,
    user: User,
    leave_type: LeaveType,
    year: int = 2026,
    allocated: Decimal = Decimal("20.00"),
    used: Decimal = Decimal("0.00"),
    reserved: Decimal = Decimal("0.00"),
) -> LeaveBalance:
    balance = LeaveBalance(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=year,
        allocated_days=allocated,
        used_days=used,
        reserved_days=reserved,
    )

    db.add(balance)
    db.flush()

    return balance


# -------------------------------------------------------------------
# Get
# -------------------------------------------------------------------


def test_get_balance_returns_existing_balance(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance = create_balance(
        db,
        user=employee,
        leave_type=leave_type,
    )

    service = BalanceAdminService(db)

    result = service.get_balance(
        balance_id=balance.id,
    )

    assert result.id == balance.id
    assert result.user_id == employee.id
    assert result.leave_type_id == leave_type.id
    assert result.year == 2026


def test_get_missing_balance_raises_error(db):
    service = BalanceAdminService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave balance not found.",
    ):
        service.get_balance(
            balance_id=999999,
        )


# -------------------------------------------------------------------
# List
# -------------------------------------------------------------------


def test_list_balances_returns_items_and_total(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    first = create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        year=2026,
    )

    second = create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        year=2027,
    )

    service = BalanceAdminService(db)

    items, total = service.list_balances(
        offset=0,
        limit=100,
    )

    ids = {item.id for item in items}

    assert total >= 2
    assert first.id in ids
    assert second.id in ids


def test_list_balances_filters_by_year(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance_2026 = create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        year=2026,
    )

    create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        year=2027,
    )

    service = BalanceAdminService(db)

    items, total = service.list_balances(
        year=2026,
        offset=0,
        limit=100,
    )

    ids = {item.id for item in items}

    assert total >= 1
    assert balance_2026.id in ids
    assert all(
        item.year == 2026
        for item in items
    )


def test_list_balances_filters_by_user(db):
    employee1 = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    employee2 = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance1 = create_balance(
        db,
        user=employee1,
        leave_type=leave_type,
    )

    create_balance(
        db,
        user=employee2,
        leave_type=leave_type,
    )

    service = BalanceAdminService(db)

    items, total = service.list_balances(
        user_id=employee1.id,
        offset=0,
        limit=100,
    )

    ids = {item.id for item in items}

    assert total >= 1
    assert balance1.id in ids
    assert all(
        item.user_id == employee1.id
        for item in items
    )


def test_list_balances_filters_by_leave_type(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    leave_type1 = create_leave_type(db)
    leave_type2 = create_leave_type(db)

    balance1 = create_balance(
        db,
        user=employee,
        leave_type=leave_type1,
    )

    create_balance(
        db,
        user=employee,
        leave_type=leave_type2,
    )

    service = BalanceAdminService(db)

    items, total = service.list_balances(
        leave_type_id=leave_type1.id,
        offset=0,
        limit=100,
    )

    ids = {item.id for item in items}

    assert total >= 1
    assert balance1.id in ids
    assert all(
        item.leave_type_id == leave_type1.id
        for item in items
    )


def test_list_balances_pagination(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        year=2026,
    )

    create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        year=2027,
    )

    create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        year=2028,
    )

    service = BalanceAdminService(db)

    items, total = service.list_balances(
        offset=1,
        limit=2,
    )

    assert total >= 3
    assert len(items) <= 2


def test_list_balances_rejects_negative_offset(db):
    service = BalanceAdminService(db)

    with pytest.raises(
        ValueError,
        match="Offset cannot be negative.",
    ):
        service.list_balances(
            offset=-1,
        )


def test_list_balances_rejects_invalid_limit(db):
    service = BalanceAdminService(db)

    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100.",
    ):
        service.list_balances(
            limit=101,
        )


# -------------------------------------------------------------------
# Create
# -------------------------------------------------------------------


def test_create_balance_for_employee(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    data = LeaveBalanceCreate(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("20.00"),
    )

    service = BalanceAdminService(db)

    result = service.create_balance(
        data=data,
    )

    assert result.id is not None
    assert result.user_id == employee.id
    assert result.leave_type_id == leave_type.id
    assert result.year == 2026
    assert result.allocated_days == Decimal("20.00")
    assert result.used_days == Decimal("0.00")
    assert result.reserved_days == Decimal("0.00")


def test_create_balance_rejects_non_employee(db):
    manager = create_user(
        db,
        role=Role.MANAGER,
    )
    leave_type = create_leave_type(db)

    data = LeaveBalanceCreate(
        user_id=manager.id,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("20.00"),
    )

    service = BalanceAdminService(db)

    with pytest.raises(
        InvalidManagerError,
        match="can only be assigned to employees",
    ):
        service.create_balance(
            data=data,
        )


def test_create_balance_rejects_missing_user(db):
    leave_type = create_leave_type(db)

    data = LeaveBalanceCreate(
        user_id=999999,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("20.00"),
    )

    service = BalanceAdminService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="User not found.",
    ):
        service.create_balance(
            data=data,
        )


def test_create_balance_rejects_missing_leave_type(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    data = LeaveBalanceCreate(
        user_id=employee.id,
        leave_type_id=999999,
        year=2026,
        allocated_days=Decimal("20.00"),
    )

    service = BalanceAdminService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave type not found.",
    ):
        service.create_balance(
            data=data,
        )


def test_create_duplicate_balance_is_rejected(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        year=2026,
    )

    data = LeaveBalanceCreate(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("20.00"),
    )

    service = BalanceAdminService(db)

    with pytest.raises(
        ResourceConflictError,
        match="already exists",
    ):
        service.create_balance(
            data=data,
        )


def test_create_zero_allowance_is_allowed(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    data = LeaveBalanceCreate(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("0.00"),
    )

    service = BalanceAdminService(db)

    result = service.create_balance(
        data=data,
    )

    assert result.allocated_days == Decimal("0.00")
    assert result.used_days == Decimal("0.00")
    assert result.reserved_days == Decimal("0.00")


# -------------------------------------------------------------------
# Update
# -------------------------------------------------------------------


def test_update_allocated_days(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance = create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("2.00"),
    )

    data = LeaveBalanceUpdate(
        allocated_days=Decimal("15.00"),
    )

    service = BalanceAdminService(db)

    result = service.update_balance(
        balance_id=balance.id,
        data=data,
    )

    assert result.allocated_days == Decimal("15.00")
    assert result.used_days == Decimal("5.00")
    assert result.reserved_days == Decimal("2.00")
    assert result.remaining_days == Decimal("8.00")


def test_update_allocation_cannot_go_below_used_plus_reserved(db):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance = create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("3.00"),
    )

    data = LeaveBalanceUpdate(
        allocated_days=Decimal("7.00"),
    )

    service = BalanceAdminService(db)

    with pytest.raises(
        InsufficientBalanceError,
        match="Allocated days cannot be less than used plus reserved",
    ):
        service.update_balance(
            balance_id=balance.id,
            data=data,
        )


def test_update_allocation_equal_to_used_plus_reserved_is_allowed(
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance = create_balance(
        db,
        user=employee,
        leave_type=leave_type,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("3.00"),
    )

    data = LeaveBalanceUpdate(
        allocated_days=Decimal("8.00"),
    )

    service = BalanceAdminService(db)

    result = service.update_balance(
        balance_id=balance.id,
        data=data,
    )

    assert result.allocated_days == Decimal("8.00")
    assert result.remaining_days == Decimal("0.00")


def test_update_missing_balance_raises_error(db):
    service = BalanceAdminService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave balance not found.",
    ):
        service.update_balance(
            balance_id=999999,
            data=LeaveBalanceUpdate(
                allocated_days=Decimal("20.00"),
            ),
        )