from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import HalfDayType, LeaveStatus
from app.schemas.leave_type import LeaveTypeResponse
from app.schemas.user import UserResponse


class LeaveRequestCreate(BaseModel):
    """
    Data required to create a leave request.
    """

    leave_type_id: int = Field(
        ...,
        gt=0,
        description="ID of the leave type.",
    )

    start_date: date = Field(
        ...,
        description="First day of leave.",
    )

    end_date: date = Field(
        ...,
        description="Last day of leave.",
    )

    start_half_day: HalfDayType = Field(
        default=HalfDayType.NONE,
        description="Half-day selection for the start date.",
    )

    end_half_day: HalfDayType = Field(
        default=HalfDayType.NONE,
        description="Half-day selection for the end date.",
    )

    reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional reason for the leave.",
    )

    @field_validator("reason")
    @classmethod
    def validate_reason(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize an optional reason.
        """
        if value is None:
            return None

        cleaned = value.strip()

        return cleaned if cleaned else None

    @model_validator(mode="after")
    def validate_dates_and_half_days(
        self,
    ) -> "LeaveRequestCreate":
        """
        Validate relationships between dates and half-day fields.
        """

        if self.end_date < self.start_date:
            raise ValueError(
                "End date cannot be before start date."
            )

        # A single-day leave request can only represent
        # one half-day selection.
        if self.start_date == self.end_date:
            if (
                self.start_half_day != HalfDayType.NONE
                and self.end_half_day != HalfDayType.NONE
            ):
                raise ValueError(
                    "For a single-day leave request, "
                    "only one half-day field can be specified."
                )

        return self


class LeaveRequestResponse(BaseModel):
    """
    Leave request returned by the API.
    """

    id: int

    user_id: int

    user: UserResponse | None = None

    leave_type_id: int

    leave_type: LeaveTypeResponse | None = None

    start_date: date

    end_date: date

    start_half_day: HalfDayType

    end_half_day: HalfDayType

    total_days: Decimal

    reason: str | None

    status: LeaveStatus

    approved_by_id: int | None

    approval_comment: str | None

    approved_at: datetime | None

    cancelled_by_id: int | None

    cancellation_reason: str | None

    cancelled_at: datetime | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class LeaveRequestAllocationResponse(BaseModel):
    """
    Year-specific allocation of a leave request.
    """

    id: int
    leave_request_id: int
    year: int
    allocated_days: Decimal
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class LeaveRequestDetailResponse(LeaveRequestResponse):
    """
    Detailed leave request response including
    yearly allocations.
    """

    allocations: list[LeaveRequestAllocationResponse] = Field(
        default_factory=list,
    )


class LeaveRequestListResponse(BaseModel):
    """
    Paginated list of leave requests.
    """

    items: list[LeaveRequestResponse]

    total: int

    offset: int = 0

    limit: int = 50

class LeaveDecisionRequest(BaseModel):
    comment: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()
        return value or None