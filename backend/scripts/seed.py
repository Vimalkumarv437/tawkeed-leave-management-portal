from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.enums import Role
from app.core.security import hash_password
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.public_holiday import PublicHoliday
from app.models.user import User


def get_required_setting(name: str) -> str:
    """
    Return a required seed setting from application configuration.
    """
    value = getattr(settings, name, None)

    if not value:
        raise RuntimeError(
            f"Required setting '{name}' is missing."
        )

    return value


def get_or_create_user(
    db,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: Role,
    manager: User | None = None,
) -> User:
    """Create a user if the email does not already exist."""

    normalized_email = email.strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=normalized_email,
            password_hash=hash_password(password),
            role=role,
            manager=manager,
            is_active=True,
        )

        db.add(user)
        db.flush()

        print(f"Created user: {normalized_email}")

    else:
        print(f"User already exists: {normalized_email}")

    return user


def get_or_create_leave_type(
    db,
    *,
    name: str,
    code: str,
    description: str,
    allowance: Decimal,
) -> LeaveType:
    """Create a leave type if it doesn't already exist."""

    leave_type = db.scalar(
        select(LeaveType).where(
            LeaveType.code == code
        )
    )

    if leave_type is None:
        leave_type = LeaveType(
            name=name,
            code=code,
            description=description,
            default_annual_allowance=allowance,
            is_active=True,
        )

        db.add(leave_type)
        db.flush()

        print(f"Created leave type: {code}")

    else:
        print(f"Leave type already exists: {code}")

    return leave_type


def get_or_create_holiday(
    db,
    *,
    holiday_date: date,
    name: str,
    description: str | None = None,
) -> PublicHoliday:
    """Create a public holiday if the date doesn't exist."""

    holiday = db.scalar(
        select(PublicHoliday).where(
            PublicHoliday.holiday_date == holiday_date
        )
    )

    if holiday is None:
        holiday = PublicHoliday(
            holiday_date=holiday_date,
            name=name,
            description=description,
        )

        db.add(holiday)
        db.flush()

        print(
            f"Created holiday: "
            f"{holiday_date} - {name}"
        )

    else:
        print(
            f"Holiday already exists: "
            f"{holiday_date}"
        )

    return holiday


def get_or_create_balance(
    db,
    *,
    user: User,
    leave_type: LeaveType,
    year: int,
    allocated_days: Decimal,
) -> LeaveBalance:
    """Create an annual leave balance if missing."""

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == user.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == year,
        )
    )

    if balance is None:
        balance = LeaveBalance(
            user_id=user.id,
            leave_type_id=leave_type.id,
            year=year,
            allocated_days=allocated_days,
            used_days=Decimal("0.00"),
            reserved_days=Decimal("0.00"),
        )

        db.add(balance)

        print(
            f"Created balance: "
            f"{user.email} / {leave_type.code} / {year}"
        )

    else:
        print(
            f"Balance already exists: "
            f"{user.email} / {leave_type.code} / {year}"
        )

    return balance


def seed() -> None:
    """Seed development/demo data."""

    db = SessionLocal()

    try:
        # -------------------------------------------------
        # Required seed credentials
        # -------------------------------------------------

        admin_email = get_required_setting("SEED_ADMIN_EMAIL")
        admin_password = get_required_setting("SEED_ADMIN_PASSWORD")

        manager_email = get_required_setting("SEED_MANAGER_EMAIL")
        manager_password = get_required_setting("SEED_MANAGER_PASSWORD")

        employee1_email = get_required_setting("SEED_EMPLOYEE1_EMAIL")
        employee1_password = get_required_setting("SEED_EMPLOYEE1_PASSWORD")

        employee2_email = get_required_setting("SEED_EMPLOYEE2_EMAIL")
        employee2_password = get_required_setting("SEED_EMPLOYEE2_PASSWORD")

        # -------------------------------------------------
        # Users
        # -------------------------------------------------

        admin = get_or_create_user(
            db,
            email=admin_email,
            password=admin_password,
            first_name="System",
            last_name="Admin",
            role=Role.ADMIN,
        )

        manager = get_or_create_user(
            db,
            email=manager_email,
            password=manager_password,
            first_name="Team",
            last_name="Manager",
            role=Role.MANAGER,
        )

        employee1 = get_or_create_user(
            db,
            email=employee1_email,
            password=employee1_password,
            first_name="John",
            last_name="Employee",
            role=Role.EMPLOYEE,
            manager=manager,
        )

        employee2 = get_or_create_user(
            db,
            email=employee2_email,
            password=employee2_password,
            first_name="Jane",
            last_name="Employee",
            role=Role.EMPLOYEE,
            manager=manager,
        )

        # -------------------------------------------------
        # Leave types
        # -------------------------------------------------

        annual_leave = get_or_create_leave_type(
            db,
            name="Annual Leave",
            code="ANNUAL",
            description="Paid annual leave.",
            allowance=Decimal("20.00"),
        )

        sick_leave = get_or_create_leave_type(
            db,
            name="Sick Leave",
            code="SICK",
            description="Leave for illness or medical needs.",
            allowance=Decimal("12.00"),
        )

        casual_leave = get_or_create_leave_type(
            db,
            name="Casual Leave",
            code="CASUAL",
            description="Leave for personal matters.",
            allowance=Decimal("10.00"),
        )

        # -------------------------------------------------
        # Leave balances
        # -------------------------------------------------

        current_year = date.today().year

        for employee in (employee1, employee2):
            get_or_create_balance(
                db,
                user=employee,
                leave_type=annual_leave,
                year=current_year,
                allocated_days=annual_leave.default_annual_allowance,
            )

            get_or_create_balance(
                db,
                user=employee,
                leave_type=sick_leave,
                year=current_year,
                allocated_days=sick_leave.default_annual_allowance,
            )

            get_or_create_balance(
                db,
                user=employee,
                leave_type=casual_leave,
                year=current_year,
                allocated_days=casual_leave.default_annual_allowance,
            )

        # -------------------------------------------------
        # Sample holidays
        # -------------------------------------------------
        #
        # These are demonstration records only.
        # Actual company holidays should be managed by Admin.

        get_or_create_holiday(
            db,
            holiday_date=date(current_year, 1, 1),
            name="New Year's Day",
            description="New Year's Day.",
        )

        get_or_create_holiday(
            db,
            holiday_date=date(current_year, 5, 1),
            name="Labour Day",
            description="Labour Day.",
        )

        get_or_create_holiday(
            db,
            holiday_date=date(current_year, 12, 25),
            name="Christmas Day",
            description="Christmas Day.",
        )

        db.commit()

        print()
        print("Seed completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed()