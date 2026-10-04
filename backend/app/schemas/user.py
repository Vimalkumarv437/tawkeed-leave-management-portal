from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.core.enums import Role


class UserCreate(BaseModel):
    """
    Data required to create a new user.

    The role must be explicitly provided.
    The backend will validate whether the authenticated
    admin is allowed to create the requested role.
    """

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    last_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
    )

    role: Role

    manager_id: int | None = Field(
        default=None,
        gt=0,
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Normalize and validate names.
        """
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        return value

    @model_validator(mode="after")
    def validate_manager_assignment(self) -> "UserCreate":
        """
        Employees may be created with a manager.
        Admins and managers should not be assigned a manager.
        """

        if self.role == Role.EMPLOYEE and self.manager_id is None:
            raise ValueError(
                "An employee must have a manager."
            )

        if self.role in {Role.ADMIN, Role.MANAGER}:
            if self.manager_id is not None:
                raise ValueError(
                    "Admins and managers cannot have a manager."
                )

        return self


class UserUpdate(BaseModel):
    """
    Data allowed when updating a user.

    All fields are optional because this is a partial update.
    """

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    email: EmailStr | None = None

    role: Role | None = None

    manager_id: int | None = Field(
        default=None,
        gt=0,
    )

    is_active: bool | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_optional_name(
        cls,
        value: str | None,
    ) -> str | None:
        """
        Normalize optional name updates.
        """
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        return value

    @model_validator(mode="after")
    def validate_optional_manager(
        self,
    ) -> "UserUpdate":
        """
        Prevent an Admin or Manager role from being assigned
        together with a manager ID.

        Full validation against the existing user's current
        role belongs in the service layer.
        """

        if (
            self.role in {Role.ADMIN, Role.MANAGER}
            and self.manager_id is not None
        ):
            raise ValueError(
                "Admins and managers cannot have a manager."
            )

        return self


class UserResponse(BaseModel):
    """
    Safe public representation of a user.

    Sensitive authentication fields are intentionally excluded.
    """

    id: int

    first_name: str

    last_name: str

    email: EmailStr

    role: Role

    manager_id: int | None

    is_active: bool

    last_login_at: datetime | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserListResponse(BaseModel):
    """
    Paginated user list response.
    """

    items: list[UserResponse]

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