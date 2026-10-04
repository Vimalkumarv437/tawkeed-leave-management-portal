from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PublicHoliday(Base):
    __tablename__ = "public_holidays"

    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) > 0",
            name="ck_public_holidays_name_not_empty",
        ),
        Index(
            "ix_public_holidays_date",
            "holiday_date",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    holiday_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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