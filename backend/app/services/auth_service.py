from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse


class AuthService:
    """
    Handles authentication business logic.

    Responsibilities:
    - Authenticate users
    - Enforce account status
    - Enforce login lockout
    - Track failed login attempts
    - Reset failed attempts after successful login
    - Create JWT access tokens
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def login(self, login_data: LoginRequest) -> TokenResponse:
        """
        Authenticate a user and return a JWT access token.
        """

        email = str(login_data.email).strip().lower()

        # Lock the user row during authentication so concurrent
        # login attempts cannot corrupt the failed-login counter.
        statement = (
            select(User)
            .where(User.email == email)
            .with_for_update()
        )

        user = self.db.scalar(statement)

        # Use a generic message so we don't reveal whether
        # an email address exists in the system.
        if user is None:
            raise AuthenticationError(
                "Invalid email or password."
            )

        # Inactive users cannot authenticate.
        if not user.is_active:
            raise AuthenticationError(
                "Invalid email or password."
            )

        now = datetime.now(timezone.utc)

        # -------------------------------------------------
        # Check account lockout
        # -------------------------------------------------

        if user.locked_until is not None:
            locked_until = user.locked_until

            # Defensive handling if the database returns
            # a naive datetime.
            if locked_until.tzinfo is None:
                locked_until = locked_until.replace(
                    tzinfo=timezone.utc
                )

            if locked_until > now:
                raise AuthenticationError(
                    "Invalid email or password."
                )

            # Lockout has expired.
            user.locked_until = None
            user.failed_login_attempts = 0

        # -------------------------------------------------
        # Verify password
        # -------------------------------------------------

        password_valid = verify_password(
            login_data.password,
            user.password_hash,
        )

        if not password_valid:
            self._record_failed_login(user, now)

            self.db.commit()

            raise AuthenticationError(
                "Invalid email or password."
            )

        # -------------------------------------------------
        # Successful login
        # -------------------------------------------------

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now

        access_token = create_access_token(
            subject=str(user.id),
            token_version=user.token_version,
        )

        self.db.commit()

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
        )

    def _record_failed_login(
        self,
        user: User,
        now: datetime,
    ) -> None:
        """
        Increment the failed-login counter and lock the
        account when the configured threshold is reached.
        """

        user.failed_login_attempts += 1

        if (
            user.failed_login_attempts
            >= settings.MAX_LOGIN_ATTEMPTS
        ):
            user.locked_until = (
                now
                + timedelta(
                    minutes=settings.LOGIN_LOCKOUT_MINUTES
                )
            )