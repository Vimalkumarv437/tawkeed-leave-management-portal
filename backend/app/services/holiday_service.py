from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.models.public_holiday import PublicHoliday


class HolidayService:
    """
    Handles public holiday database operations.

    Responsibilities:
    - Retrieve holidays for a date range
    - Check whether a date is a public holiday
    - Create holidays
    - Update holidays
    - Delete holidays
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ---------------------------------------------------------
    # Read operations
    # ---------------------------------------------------------

    def get_holiday_dates(
        self,
        start_date: date,
        end_date: date,
    ) -> set[date]:
        """
        Return public holiday dates within an inclusive range.

        This method returns only the dates because the working-day
        calculation does not need the full PublicHoliday objects.
        """

        if end_date < start_date:
            raise ValueError(
                "End date cannot be before start date."
            )

        statement = (
            select(PublicHoliday.holiday_date)
            .where(
                PublicHoliday.holiday_date >= start_date,
                PublicHoliday.holiday_date <= end_date,
            )
            .order_by(PublicHoliday.holiday_date)
        )

        holiday_dates = self.db.scalars(statement).all()

        return set(holiday_dates)

    def is_public_holiday(
        self,
        holiday_date: date,
    ) -> bool:
        """
        Check whether a specific date is a public holiday.
        """

        statement = select(PublicHoliday.id).where(
            PublicHoliday.holiday_date == holiday_date
        )

        return self.db.scalar(statement) is not None

    def get_holiday(
        self,
        holiday_id: int,
    ) -> PublicHoliday:
        """
        Retrieve a holiday by ID.
        """

        holiday = self.db.get(
            PublicHoliday,
            holiday_id,
        )

        if holiday is None:
            raise ResourceNotFoundError(
                "Public holiday not found."
            )

        return holiday

    def list_holidays(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[PublicHoliday]:
        """
        Return public holidays, optionally filtered by date range.
        """

        statement = select(PublicHoliday)

        if start_date is not None:
            statement = statement.where(
                PublicHoliday.holiday_date >= start_date
            )

        if end_date is not None:
            statement = statement.where(
                PublicHoliday.holiday_date <= end_date
            )

        if (
            start_date is not None
            and end_date is not None
            and end_date < start_date
        ):
            raise ValueError(
                "End date cannot be before start date."
            )

        statement = statement.order_by(
            PublicHoliday.holiday_date
        )

        return list(
            self.db.scalars(statement).all()
        )

    # ---------------------------------------------------------
    # Create
    # ---------------------------------------------------------

    def create_holiday(
        self,
        *,
        holiday_date: date,
        name: str,
        description: str | None = None,
    ) -> PublicHoliday:
        """
        Create a public holiday.

        The database has a unique constraint on holiday_date,
        so the same date cannot be inserted twice.
        """

        existing = self.db.scalar(
            select(PublicHoliday.id).where(
                PublicHoliday.holiday_date == holiday_date
            )
        )

        if existing is not None:
            raise ResourceConflictError(
                "A public holiday already exists for this date."
            )

        holiday = PublicHoliday(
            holiday_date=holiday_date,
            name=name.strip(),
            description=(
                description.strip()
                if description
                else None
            ),
        )

        self.db.add(holiday)

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

            # Protect against a race condition where another
            # transaction inserts the same date at the same time.
            raise ResourceConflictError(
                "A public holiday already exists for this date."
            )

        self.db.refresh(holiday)

        return holiday

    # ---------------------------------------------------------
    # Update
    # ---------------------------------------------------------

    def update_holiday(
        self,
        holiday_id: int,
        *,
        holiday_date: date | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> PublicHoliday:
        """
        Update an existing public holiday.
        """

        holiday = self.get_holiday(holiday_id)

        if holiday_date is not None:
            existing = self.db.scalar(
                select(PublicHoliday.id).where(
                    PublicHoliday.holiday_date == holiday_date,
                    PublicHoliday.id != holiday_id,
                )
            )

            if existing is not None:
                raise ResourceConflictError(
                    "A public holiday already exists for this date."
                )

            holiday.holiday_date = holiday_date

        if name is not None:
            cleaned_name = name.strip()

            if not cleaned_name:
                raise ValueError(
                    "Holiday name cannot be empty."
                )

            holiday.name = cleaned_name

        if description is not None:
            holiday.description = (
                description.strip()
                if description.strip()
                else None
            )

        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()

            raise ResourceConflictError(
                "A public holiday already exists for this date."
            )

        self.db.refresh(holiday)

        return holiday

    # ---------------------------------------------------------
    # Delete
    # ---------------------------------------------------------

    def delete_holiday(
        self,
        holiday_id: int,
    ) -> None:
        """
        Delete a public holiday.
        """

        holiday = self.get_holiday(holiday_id)

        self.db.delete(holiday)
        self.db.commit()