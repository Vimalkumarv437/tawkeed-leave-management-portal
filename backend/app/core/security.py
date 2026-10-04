from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings

# Password hashing

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using Argon2 for secure authentication
    The plain-text password is never stored in the database.
    """
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain-text password against its stored hash.
    """
    return password_hash.verify(
        plain_password,
        hashed_password,
    )

# JWT access tokens


def create_access_token(
    subject: str,
    token_version: int,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:
            User ID stored in the JWT `sub` claim.

        token_version:
            Used to invalidate previously issued tokens.

        expires_delta:
            Optional custom expiration period.
            If omitted, the configured value is used.
    """

    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": expire,
        "type": "access",
        "ver": token_version,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Raises:
        JWTError:
            If the token is invalid, expired, malformed,
            or has an invalid token type.
    """

    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )

    # Only access tokens are accepted here.
    if payload.get("type") != "access":
        raise JWTError("Invalid token type.")

    # Every access token must have a subject.
    if not payload.get("sub"):
        raise JWTError("Token subject is missing.")

    return payload