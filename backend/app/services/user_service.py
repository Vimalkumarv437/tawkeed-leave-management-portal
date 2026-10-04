from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import AuditAction, Role
from app.core.exceptions import (
    AuthorizationError,
    InvalidManagerError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.audit_service import AuditService


class UserService:
    """
    Handles administrator user-management operations.

    Responsibilities:
    - Create users
    - List users
    - Get users
    - Update users
    - Validate manager assignments
    - Deactivate users
    - Record audit events

    Transaction management is intentionally left to the caller.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_service = AuditService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_email(email: str) -> str:
        return email.strip().lower()

    @staticmethod
    def _normalize_name(value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        return value

    def _get_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)

        if user is None:
            raise ResourceNotFoundError("User not found.")

        return user

    def _validate_manager(
        self,
        *,
        manager_id: int,
        employee_user_id: int | None = None,
    ) -> User:
        """
        Validate that manager_id points to an active manager.

        A user cannot be assigned to themselves.
        """

        if employee_user_id is not None and manager_id == employee_user_id:
            raise InvalidManagerError(
                "A user cannot be assigned as their own manager."
            )

        manager = self._get_user(manager_id)

        if manager.role != Role.MANAGER:
            raise InvalidManagerError(
                "The assigned manager must have MANAGER role."
            )

        if not manager.is_active:
            raise InvalidManagerError(
                "The assigned manager is inactive."
            )

        return manager

    def _ensure_email_available(
        self,
        *,
        email: str,
        exclude_user_id: int | None = None,
    ) -> None:
        statement = select(User).where(
            func.lower(User.email) == email.lower()
        )

        if exclude_user_id is not None:
            statement = statement.where(
                User.id != exclude_user_id
            )

        existing = self.db.scalar(statement)

        if existing is not None:
            raise ResourceConflictError(
                "A user with this email already exists."
            )

    # ------------------------------------------------------------------
    # Get
    # ------------------------------------------------------------------

    def get_user(
        self,
        *,
        user_id: int,
    ) -> User:
        return self._get_user(user_id)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_users(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        role: Role | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        if offset < 0:
            raise ValueError(
                "Offset cannot be negative."
            )

        if limit < 1 or limit > 100:
            raise ValueError(
                "Limit must be between 1 and 100."
            )

        filters: list[Any] = []

        if role is not None:
            filters.append(User.role == role)

        if is_active is not None:
            filters.append(User.is_active.is_(is_active))

        total_statement = select(
            func.count(User.id)
        ).where(*filters)

        total = self.db.scalar(total_statement) or 0

        statement = (
            select(User)
            .where(*filters)
            .order_by(User.id)
            .offset(offset)
            .limit(limit)
        )

        users = list(
            self.db.scalars(statement).all()
        )

        return users, total

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_user(
        self,
        *,
        data: UserCreate,
        actor_user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        email = self._normalize_email(data.email)

        self._ensure_email_available(
            email=email,
        )

        first_name = self._normalize_name(
            data.first_name
        )
        last_name = self._normalize_name(
            data.last_name
        )

        manager_id: int | None = data.manager_id

        if data.role == Role.EMPLOYEE:
            if manager_id is None:
                raise InvalidManagerError(
                    "Employees must have a manager."
                )

            self._validate_manager(
                manager_id=manager_id,
            )

        else:
            if manager_id is not None:
                raise InvalidManagerError(
                    "Only employees can be assigned a manager."
                )

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hash_password(data.password),
            role=data.role,
            manager_id=manager_id,
            is_active=True,
        )

        self.db.add(user)
        self.db.flush()

        self.audit_service.log(
            user_id=actor_user_id,
            action=AuditAction.CREATE_USER,
            entity_type="user",
            entity_id=user.id,
            details={
                "email": user.email,
                "role": user.role.value,
                "manager_id": user.manager_id,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.flush()

        return user

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_user(
        self,
        *,
        user_id: int,
        data: UserUpdate,
        actor_user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        user = self._get_user(user_id)

        if data.email is not None:
            email = self._normalize_email(data.email)

            if email != user.email.lower():
                self._ensure_email_available(
                    email=email,
                    exclude_user_id=user.id,
                )

                user.email = email

        if data.first_name is not None:
            user.first_name = self._normalize_name(
                data.first_name
            )

        if data.last_name is not None:
            user.last_name = self._normalize_name(
                data.last_name
            )

        old_role = user.role
        old_manager_id = user.manager_id
        old_is_active = user.is_active

        requested_role = (
            data.role
            if data.role is not None
            else user.role
        )

        requested_manager_id = (
            data.manager_id
            if data.manager_id is not None
            else user.manager_id
        )

        # --------------------------------------------------------------
        # Role / manager rules
        # --------------------------------------------------------------

        if requested_role == Role.EMPLOYEE:
            if requested_manager_id is None:
                raise InvalidManagerError(
                    "Employees must have a manager."
                )

            self._validate_manager(
                manager_id=requested_manager_id,
                employee_user_id=user.id,
            )

        else:
            if requested_manager_id is not None:
                raise InvalidManagerError(
                    "Only employees can be assigned a manager."
                )

            requested_manager_id = None

        user.role = requested_role
        user.manager_id = requested_manager_id

        if data.is_active is not None:
            user.is_active = data.is_active

        changes: dict[str, Any] = {}

        if old_role != user.role:
            changes["role"] = {
                "from": old_role.value,
                "to": user.role.value,
            }

        if old_manager_id != user.manager_id:
            changes["manager_id"] = {
                "from": old_manager_id,
                "to": user.manager_id,
            }

        if old_is_active != user.is_active:
            changes["is_active"] = {
                "from": old_is_active,
                "to": user.is_active,
            }

        if data.email is not None:
            changes["email"] = user.email

        if data.first_name is not None:
            changes["first_name"] = user.first_name

        if data.last_name is not None:
            changes["last_name"] = user.last_name

        if changes:
            self.audit_service.log(
                user_id=actor_user_id,
                action=AuditAction.UPDATE_USER,
                entity_type="user",
                entity_id=user.id,
                details=changes,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        self.db.flush()

        return user

    # ------------------------------------------------------------------
    # Deactivate
    # ------------------------------------------------------------------

    def deactivate_user(
        self,
        *,
        user_id: int,
        actor_user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        user = self._get_user(user_id)

        if user.id == actor_user_id:
            raise AuthorizationError(
                "An administrator cannot deactivate their own account."
            )

        if not user.is_active:
            raise ResourceConflictError(
                "User is already inactive."
            )

        user.is_active = False

        self.audit_service.log(
            user_id=actor_user_id,
            action=AuditAction.DEACTIVATE_USER,
            entity_type="user",
            entity_id=user.id,
            details={
                "email": user.email,
                "role": user.role.value,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.flush()

        return user

    # ------------------------------------------------------------------
    # Reactivate
    # ------------------------------------------------------------------

    def reactivate_user(
        self,
        *,
        user_id: int,
        actor_user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> User:
        user = self._get_user(user_id)

        if user.is_active:
            raise ResourceConflictError(
                "User is already active."
            )

        user.is_active = True

        self.audit_service.log(
            user_id=actor_user_id,
            action=AuditAction.UPDATE_USER,
            entity_type="user",
            entity_id=user.id,
            details={
                "is_active": {
                    "from": False,
                    "to": True,
                }
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.flush()

        return user