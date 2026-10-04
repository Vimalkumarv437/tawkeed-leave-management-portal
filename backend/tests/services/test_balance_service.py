from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.core.enums import Role
from app.core.exceptions import (
    InsufficientBalanceError,
    ResourceNotFoundError,
)
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.user import User
from app.services.balance_service import BalanceService


def create_test_user(db, email: str = "balance-test@example.com") -> User:
    user = User(
        first_name="Balance",
        last_name="Tester",
        email=email,
        password_hash="test-hash",
        role=Role.EMPLOYEE,
    )

    db.add(user)
    db.flush()

    return user


def create_test_leave_type(
    db,
    code: str = "TEST_BALANCE",
) -> LeaveType:
    leave_type = LeaveType(
        name=f"Test Balance Leave {code}",
        code=code,
        default_annual_allowance=Decimal("20.00"),
        is_active=True,
    )

    db.add(leave_type)
    db.flush()

    return leave_type


def create_test_balance(
    db,
    *,
    allocated: Decimal = Decimal("20.00"),
    used: Decimal = Decimal("5.00"),
    reserved: Decimal = Decimal("0.00"),
    year: int = 2026,
):
    user = create_test_user(
        db,
        email=f"balance-{year}-{allocated}-{used}-{reserved}@example.com",
    )

    leave_type = create_test_leave_type(
        db,
        code=f"BAL{year}{int(allocated * 100)}{int(used * 100)}{int(reserved * 100)}",
    )

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

    return user, leave_type, balance


# -------------------------------------------------------------------
# Read operations
# -------------------------------------------------------------------


def test_get_balance_returns_existing_balance(db):
    user, leave_type, balance = create_test_balance(db)

    service = BalanceService(db)

    result = service.get_balance(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
    )

    assert result.id == balance.id
    assert result.allocated_days == Decimal("20.00")
    assert result.used_days == Decimal("5.00")
    assert result.reserved_days == Decimal("0.00")


def test_get_balance_missing_balance_raises_error(db):
    service = BalanceService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave balance not found.",
    ):
        service.get_balance(
            user_id=999999,
            leave_type_id=999999,
            year=2026,
        )


def test_get_remaining_days_returns_available_balance(db):
    user, leave_type, _ = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("3.00"),
    )

    service = BalanceService(db)

    result = service.get_remaining_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
    )

    assert result == Decimal("12.00")


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------


def test_validate_days_accepts_one_day():
    result = BalanceService._validate_days(Decimal("1.00"))

    assert result == Decimal("1.00")


def test_validate_days_accepts_half_day():
    result = BalanceService._validate_days(Decimal("0.50"))

    assert result == Decimal("0.50")


def test_validate_days_rejects_zero():
    with pytest.raises(
        ValueError,
        match="Leave days must be greater than zero.",
    ):
        BalanceService._validate_days(Decimal("0.00"))


def test_validate_days_rejects_negative_value():
    with pytest.raises(
        ValueError,
        match="Leave days must be greater than zero.",
    ):
        BalanceService._validate_days(Decimal("-1.00"))


def test_validate_days_rejects_quarter_day():
    with pytest.raises(
        ValueError,
        match="Leave days must be in 0.5-day increments.",
    ):
        BalanceService._validate_days(Decimal("0.25"))


# -------------------------------------------------------------------
# Reserve
# -------------------------------------------------------------------


def test_reserve_days_increases_reserved_balance(db):
    user, leave_type, balance = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("0.00"),
    )

    service = BalanceService(db)

    result = service.reserve_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("3.00"),
    )

    assert result.reserved_days == Decimal("3.00")
    assert result.used_days == Decimal("5.00")
    assert result.remaining_days == Decimal("12.00")


def test_reserve_half_day(db):
    user, leave_type, balance = create_test_balance(db)

    service = BalanceService(db)

    result = service.reserve_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("0.50"),
    )

    assert result.reserved_days == Decimal("0.50")


def test_reserve_exact_remaining_balance(db):
    user, leave_type, balance = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("0.00"),
    )

    service = BalanceService(db)

    result = service.reserve_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("15.00"),
    )

    assert result.reserved_days == Decimal("15.00")
    assert result.remaining_days == Decimal("0.00")


def test_reserve_insufficient_balance_raises_error(db):
    user, leave_type, balance = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("0.00"),
    )

    service = BalanceService(db)

    with pytest.raises(
        InsufficientBalanceError,
        match="Insufficient leave balance.",
    ):
        service.reserve_days(
            user_id=user.id,
            leave_type_id=leave_type.id,
            year=2026,
            days=Decimal("15.50"),
        )


def test_reserve_zero_days_raises_error(db):
    user, leave_type, balance = create_test_balance(db)

    service = BalanceService(db)

    with pytest.raises(
        ValueError,
        match="Leave days must be greater than zero.",
    ):
        service.reserve_days(
            user_id=user.id,
            leave_type_id=leave_type.id,
            year=2026,
            days=Decimal("0.00"),
        )


# -------------------------------------------------------------------
# Release reservation
# -------------------------------------------------------------------


def test_release_reserved_days_decreases_reservation(db):
    user, leave_type, balance = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("4.00"),
    )

    service = BalanceService(db)

    result = service.release_reserved_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("2.00"),
    )

    assert result.reserved_days == Decimal("2.00")
    assert result.used_days == Decimal("5.00")
    assert result.remaining_days == Decimal("13.00")


def test_release_all_reserved_days(db):
    user, leave_type, balance = create_test_balance(
        db,
        reserved=Decimal("4.00"),
    )

    service = BalanceService(db)

    result = service.release_reserved_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("4.00"),
    )

    assert result.reserved_days == Decimal("0.00")


def test_release_more_than_reserved_raises_error(db):
    user, leave_type, balance = create_test_balance(
        db,
        reserved=Decimal("2.00"),
    )

    service = BalanceService(db)

    with pytest.raises(
        ValueError,
        match="Reserved balance is insufficient.",
    ):
        service.release_reserved_days(
            user_id=user.id,
            leave_type_id=leave_type.id,
            year=2026,
            days=Decimal("2.50"),
        )


# -------------------------------------------------------------------
# Approval
# -------------------------------------------------------------------


def test_approve_reserved_days_moves_reserved_to_used(db):
    user, leave_type, balance = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("3.00"),
    )

    service = BalanceService(db)

    result = service.approve_reserved_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("3.00"),
    )

    assert result.reserved_days == Decimal("0.00")
    assert result.used_days == Decimal("8.00")
    assert result.remaining_days == Decimal("12.00")


def test_approve_reserved_days_partial_amount(db):
    user, leave_type, balance = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
        reserved=Decimal("4.00"),
    )

    service = BalanceService(db)

    result = service.approve_reserved_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("1.50"),
    )

    assert result.reserved_days == Decimal("2.50")
    assert result.used_days == Decimal("6.50")


def test_approve_more_than_reserved_raises_error(db):
    user, leave_type, balance = create_test_balance(
        db,
        reserved=Decimal("2.00"),
    )

    service = BalanceService(db)

    with pytest.raises(
        ValueError,
        match="Reserved balance is insufficient.",
    ):
        service.approve_reserved_days(
            user_id=user.id,
            leave_type_id=leave_type.id,
            year=2026,
            days=Decimal("2.50"),
        )


# -------------------------------------------------------------------
# Restore used balance
# -------------------------------------------------------------------


def test_restore_used_days_decreases_used_balance(db):
    user, leave_type, balance = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("8.00"),
        reserved=Decimal("0.00"),
    )

    service = BalanceService(db)

    result = service.restore_used_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("3.00"),
    )

    assert result.used_days == Decimal("5.00")
    assert result.reserved_days == Decimal("0.00")
    assert result.remaining_days == Decimal("15.00")


def test_restore_all_used_days(db):
    user, leave_type, balance = create_test_balance(
        db,
        allocated=Decimal("20.00"),
        used=Decimal("5.00"),
    )

    service = BalanceService(db)

    result = service.restore_used_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("5.00"),
    )

    assert result.used_days == Decimal("0.00")
    assert result.remaining_days == Decimal("20.00")


def test_restore_more_than_used_raises_error(db):
    user, leave_type, balance = create_test_balance(
        db,
        used=Decimal("2.00"),
    )

    service = BalanceService(db)

    with pytest.raises(
        ValueError,
        match="Used balance is insufficient.",
    ):
        service.restore_used_days(
            user_id=user.id,
            leave_type_id=leave_type.id,
            year=2026,
            days=Decimal("2.50"),
        )


# -------------------------------------------------------------------
# Missing balance handling for write operations
# -------------------------------------------------------------------


def test_reserve_missing_balance_raises_error(db):
    service = BalanceService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave balance not found.",
    ):
        service.reserve_days(
            user_id=999999,
            leave_type_id=999999,
            year=2026,
            days=Decimal("1.00"),
        )


def test_release_missing_balance_raises_error(db):
    service = BalanceService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave balance not found.",
    ):
        service.release_reserved_days(
            user_id=999999,
            leave_type_id=999999,
            year=2026,
            days=Decimal("1.00"),
        )


def test_approve_missing_balance_raises_error(db):
    service = BalanceService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave balance not found.",
    ):
        service.approve_reserved_days(
            user_id=999999,
            leave_type_id=999999,
            year=2026,
            days=Decimal("1.00"),
        )


def test_restore_missing_balance_raises_error(db):
    service = BalanceService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave balance not found.",
    ):
        service.restore_used_days(
            user_id=999999,
            leave_type_id=999999,
            year=2026,
            days=Decimal("1.00"),
        )


# -------------------------------------------------------------------
# Multiple years
# -------------------------------------------------------------------


def test_different_year_balances_are_independent(db):
    user = create_test_user(
        db,
        email="multi-year-balance@example.com",
    )

    leave_type = create_test_leave_type(
        db,
        code="MULTIYEAR",
    )

    balance_2026 = LeaveBalance(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("20.00"),
        used_days=Decimal("5.00"),
        reserved_days=Decimal("0.00"),
    )

    balance_2027 = LeaveBalance(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2027,
        allocated_days=Decimal("20.00"),
        used_days=Decimal("2.00"),
        reserved_days=Decimal("0.00"),
    )

    db.add_all([balance_2026, balance_2027])
    db.flush()

    service = BalanceService(db)

    result_2026 = service.reserve_days(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2026,
        days=Decimal("3.00"),
    )

    result_2027 = service.get_balance(
        user_id=user.id,
        leave_type_id=leave_type.id,
        year=2027,
    )

    assert result_2026.reserved_days == Decimal("3.00")
    assert result_2026.remaining_days == Decimal("12.00")

    assert result_2027.used_days == Decimal("2.00")
    assert result_2027.reserved_days == Decimal("0.00")
    assert result_2027.remaining_days == Decimal("18.00")


# -------------------------------------------------------------------
# Row locking
# -------------------------------------------------------------------


def test_get_balance_for_update_uses_row_lock():
    mock_db = MagicMock()

    balance = MagicMock()
    mock_db.scalar.return_value = balance

    service = BalanceService(mock_db)

    result = service._get_balance_for_update(
        user_id=1,
        leave_type_id=1,
        year=2026,
    )

    assert result is balance

    statement = mock_db.scalar.call_args.args[0]

    assert statement._for_update_arg is not None