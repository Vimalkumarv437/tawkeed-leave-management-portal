from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Iterable

from app.core.enums import HalfDayType


def calculate_working_days(
    start_date: date,
    end_date: date,
    holidays: Iterable[date] | None = None,
    start_half_day: HalfDayType = HalfDayType.NONE,
    end_half_day: HalfDayType = HalfDayType.NONE,
) -> Decimal:
    """
    Calculate the number of working leave days between two dates.

    Rules:
    - Monday-Friday are working days.
    - Saturday and Sunday are excluded.
    - Public holidays are excluded.
    - A half-day on the first working day reduces the total by 0.5.
    - A half-day on the last working day reduces the total by 0.5.
    - The result is returned as Decimal for accurate day calculations.

    Args:
        start_date: First date of the leave period.
        end_date: Last date of the leave period.
        holidays: Public holiday dates to exclude.
        start_half_day: Half-day setting for the start date.
        end_half_day: Half-day setting for the end date.

    Raises:
        ValueError: If the date range is invalid or the half-day
                    configuration is invalid.
    """

    if end_date < start_date:
        raise ValueError("End date cannot be before start date.")

    if start_half_day not in HalfDayType:
        raise ValueError("Invalid start half-day value.")

    if end_half_day not in HalfDayType:
        raise ValueError("Invalid end half-day value.")

    holiday_dates = set(holidays or [])

    # ---------------------------------------------------------
    # Calculate full working days
    # ---------------------------------------------------------

    working_days = Decimal("0.00")

    current_date = start_date

    while current_date <= end_date:
        is_weekend = current_date.weekday() >= 5
        is_holiday = current_date in holiday_dates

        if not is_weekend and not is_holiday:
            working_days += Decimal("1.00")

        current_date += timedelta(days=1)

    # No working days means there is no leave to calculate.
    if working_days == Decimal("0.00"):
        if (
            start_half_day != HalfDayType.NONE
            or end_half_day != HalfDayType.NONE
        ):
            raise ValueError(
                "Half-day leave cannot be applied to "
                "a non-working day."
            )

        return Decimal("0.00")

    # ---------------------------------------------------------
    # Single-day leave
    # ---------------------------------------------------------

    if start_date == end_date:
        if start_date.weekday() >= 5 or start_date in holiday_dates:
            if (
                start_half_day != HalfDayType.NONE
                or end_half_day != HalfDayType.NONE
            ):
                raise ValueError(
                    "Half-day leave cannot be applied to "
                    "a non-working day."
                )

            return Decimal("0.00")

        # For a single working day, either half-day field
        # indicates that only half of that day is requested.
        if (
            start_half_day != HalfDayType.NONE
            and end_half_day != HalfDayType.NONE
        ):
            raise ValueError(
                "For single-day leave, only one half-day "
                "field should be specified."
            )

        if (
            start_half_day != HalfDayType.NONE
            or end_half_day != HalfDayType.NONE
        ):
            return Decimal("0.50")

        return Decimal("1.00")

    # ---------------------------------------------------------
    # Multi-day leave
    # ---------------------------------------------------------

    if (
        start_half_day != HalfDayType.NONE
        and start_date.weekday() < 5
        and start_date not in holiday_dates
    ):
        working_days -= Decimal("0.50")

    if (
        end_half_day != HalfDayType.NONE
        and end_date.weekday() < 5
        and end_date not in holiday_dates
    ):
        working_days -= Decimal("0.50")

    return max(working_days, Decimal("0.00"))