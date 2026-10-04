from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.core.enums import Role

class LoginRequest(BaseModel):
    """
    Data required to authenticate a user.
    """

    email: EmailStr = Field(
        ...,
        description="User's registered email address.",
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password.",
    )


class TokenResponse(BaseModel):
    """
    JWT access token returned after successful authentication.
    """

    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    """
    Safe user information returned to the frontend.

    Password hash and other sensitive authentication fields
    are intentionally not exposed.
    """

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    role: Role
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True,
    )