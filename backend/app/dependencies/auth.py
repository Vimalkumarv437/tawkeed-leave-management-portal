from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from jose import JWTError
from app.core.security import decode_access_token
from app.dependencies.database import get_db
from app.models.user import User


# HTTP Bearer authentication scheme.
#
# auto_error=False allows us to return our own consistent
# 401 response instead of FastAPI returning a default error.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    """
    Identify and validate the user making the request.

    Authentication flow:
        1. Read HTTP-only cookie `access_token` or Bearer token header.
        2. Decode and validate JWT.
        3. Extract user ID from `sub`.
        4. Load the user from PostgreSQL.
        5. Verify the account is active.
        6. Verify token version.
        7. Return the current User.
    """

    # -----------------------------------------------------
    # Extract token from Cookie or Authorization header
    # -----------------------------------------------------

    token: str | None = None

    if "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    elif credentials is not None:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # -----------------------------------------------------
    # Decode JWT
    # -----------------------------------------------------

    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # -----------------------------------------------------
    # Extract user ID
    # -----------------------------------------------------

    subject = payload.get("sub")

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # -----------------------------------------------------
    # Find user
    # -----------------------------------------------------

    statement = select(User).where(User.id == user_id)
    user = db.scalar(statement)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # -----------------------------------------------------
    # Check account status
    # -----------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # -----------------------------------------------------
    # Check token version
    # -----------------------------------------------------

    token_version = payload.get("ver")

    if token_version is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user