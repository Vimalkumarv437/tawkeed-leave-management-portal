from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LeaveTypeCreate(BaseModel):
    """
    Data required to create a leave type.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        pattern=r"^[A-Za-z][A-Za-z0-9_-]*$",
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    default_annual_allowance: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        le=Decimal("9999.99"),
    )

    is_active: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Leave type name cannot be empty."
            )

        return value

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        value = value.strip().upper()

        if not value:
            raise ValueError(
                "Leave type code cannot be empty."
            )

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value if value else None


class LeaveTypeUpdate(BaseModel):
    """
    Data allowed when updating a leave type.

    The code is intentionally immutable because it is
    the stable business identifier.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    default_annual_allowance: Decimal | None = Field(
        default=None,
        ge=Decimal("0.00"),
        le=Decimal("9999.99"),
    )

    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Leave type name cannot be empty."
            )

        return value

    @field_validator("description")
    @classmethod
    def normalize_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value if value else None


class LeaveTypeResponse(BaseModel):
    """
    Public API representation of a leave type.
    """

    id: int

    name: str

    code: str

    description: str | None

    default_annual_allowance: Decimal

    is_active: bool

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class LeaveTypeListResponse(BaseModel):
    """
    Paginated leave type list response.
    """

    items: list[LeaveTypeResponse]

    total: int = Field(
        ...,
        ge=0,
    )

    offset: int = Field(
        default=0,
        ge=0,
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=100,
    )