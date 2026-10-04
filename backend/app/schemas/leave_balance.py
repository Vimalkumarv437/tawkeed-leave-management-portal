from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict,  Field, field_validator


class LeaveBalanceCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    leave_type_id: int = Field(..., gt=0)
    year: int = Field(..., ge=2000, le=2100)
    allocated_days: Decimal = Field(..., ge=0)

    @field_validator("allocated_days")
    @classmethod
    def validate_allocated_days(cls, value: Decimal) -> Decimal:
        value = Decimal(value)

        if value < Decimal("0.00"):
            raise ValueError(
                "Allocated days cannot be negative."
            )

        if (value * Decimal("2")) % Decimal("1") != 0:
            raise ValueError(
                "Allocated days must be in 0.5-day increments."
            )

        return value



class LeaveBalanceUpdate(BaseModel):
    allocated_days: Decimal = Field(..., ge=0)

    @field_validator("allocated_days")
    @classmethod
    def validate_allocated_days(cls, value: Decimal) -> Decimal:
        value = Decimal(value)

        if value < Decimal("0.00"):
            raise ValueError(
                "Allocated days cannot be negative."
            )

        if (value * Decimal("2")) % Decimal("1") != 0:
            raise ValueError(
                "Allocated days must be in 0.5-day increments."
            )

        return value




class LeaveBalanceResponse(BaseModel):
    """
    Leave balance information for an employee.
    """

    id: int

    user_id: int

    leave_type_id: int

    year: int = Field(
        ...,
        ge=2000,
        le=2100,
    )

    allocated_days: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
    )

    used_days: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
    )

    reserved_days: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
    )

    remaining_days: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


class LeaveBalanceListResponse(BaseModel):
    items: list[LeaveBalanceResponse]
    total: int
    offset: int
    limit: int
    year: int | None = Field(
        default=None,
        ge=2000,
        le=2100,
    )