from datetime import date
from decimal import Decimal

import pytest

from app.core.enums import HalfDayType
from app.services.working_days import calculate_working_days


def test_monday_to_friday_returns_five_days():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 9),
    )

    assert result == Decimal("5.00")


def test_single_working_day_returns_one_day():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 5),
    )

    assert result == Decimal("1.00")


def test_weekend_days_are_excluded():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 11),
    )

    assert result == Decimal("5.00")


def test_weekend_only_range_returns_zero():
    result = calculate_working_days(
        start_date=date(2026, 10, 10),
        end_date=date(2026, 10, 11),
    )

    assert result == Decimal("0.00")


def test_public_holiday_is_excluded():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 9),
        holidays={date(2026, 10, 7)},
    )

    assert result == Decimal("4.00")


def test_multiple_public_holidays_are_excluded():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 9),
        holidays={
            date(2026, 10, 6),
            date(2026, 10, 8),
        },
    )

    assert result == Decimal("3.00")


def test_range_with_only_holidays_and_weekends_returns_zero():
    result = calculate_working_days(
        start_date=date(2026, 10, 10),
        end_date=date(2026, 10, 12),
        holidays={date(2026, 10, 12)},
    )

    assert result == Decimal("0.00")


def test_first_half_single_day_returns_half_day():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 5),
        start_half_day=HalfDayType.FIRST_HALF,
        end_half_day=HalfDayType.NONE,
    )

    assert result == Decimal("0.50")


def test_second_half_single_day_returns_half_day():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 5),
        start_half_day=HalfDayType.SECOND_HALF,
        end_half_day=HalfDayType.NONE,
    )

    assert result == Decimal("0.50")


def test_single_day_both_different_half_days_are_invalid():
    with pytest.raises(ValueError):
        calculate_working_days(
            start_date=date(2026, 10, 5),
            end_date=date(2026, 10, 5),
            start_half_day=HalfDayType.FIRST_HALF,
            end_half_day=HalfDayType.SECOND_HALF,
        )


def test_invalid_date_range_raises_error():
    with pytest.raises(ValueError):
        calculate_working_days(
            start_date=date(2026, 10, 10),
            end_date=date(2026, 10, 5),
        )


def test_multiday_leave_with_start_half_day():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 7),
        start_half_day=HalfDayType.FIRST_HALF,
        end_half_day=HalfDayType.NONE,
    )

    assert result == Decimal("2.50")


def test_multiday_leave_with_end_half_day():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 7),
        start_half_day=HalfDayType.NONE,
        end_half_day=HalfDayType.FIRST_HALF,
    )

    assert result == Decimal("2.50")


def test_multiday_leave_with_both_half_days():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 7),
        start_half_day=HalfDayType.FIRST_HALF,
        end_half_day=HalfDayType.SECOND_HALF,
    )

    assert result == Decimal("2.00")


def test_holiday_endpoint_does_not_count_as_half_day():
    result = calculate_working_days(
        start_date=date(2026, 10, 5),
        end_date=date(2026, 10, 7),
        holidays={date(2026, 10, 5)},
        start_half_day=HalfDayType.FIRST_HALF,
    )

    assert result == Decimal("2.00")