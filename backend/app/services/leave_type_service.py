from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import AuditAction
from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.models.leave_type import LeaveType
from app.schemas.leave_type import LeaveTypeCreate, LeaveTypeUpdate
from app.services.audit_service import AuditService


class LeaveTypeService:
    """
    Handles administrator leave-type management.

    Transaction management is intentionally left to the caller.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_service = AuditService(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_name(value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Leave type name cannot be empty.")

        return value

    @staticmethod
    def _normalize_code(value: str) -> str:
        value = value.strip().upper()

        if not value:
            raise ValueError("Leave type code cannot be empty.")

        return value

    def _get_leave_type(self, leave_type_id: int) -> LeaveType:
        leave_type = self.db.get(LeaveType, leave_type_id)

        if leave_type is None:
            raise ResourceNotFoundError(
                "Leave type not found."
            )

        return leave_type

    def _ensure_name_available(
        self,
        *,
        name: str,
        exclude_id: int | None = None,
    ) -> None:
        statement = select(LeaveType).where(
            func.lower(LeaveType.name) == name.lower()
        )

        if exclude_id is not None:
            statement = statement.where(
                LeaveType.id != exclude_id
            )

        if self.db.scalar(statement) is not None:
            raise ResourceConflictError(
                "A leave type with this name already exists."
            )

    def _ensure_code_available(
        self,
        *,
        code: str,
        exclude_id: int | None = None,
    ) -> None:
        statement = select(LeaveType).where(
            func.upper(LeaveType.code) == code.upper()
        )

        if exclude_id is not None:
            statement = statement.where(
                LeaveType.id != exclude_id
            )

        if self.db.scalar(statement) is not None:
            raise ResourceConflictError(
                "A leave type with this code already exists."
            )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_leave_type(
        self,
        *,
        leave_type_id: int,
    ) -> LeaveType:
        return self._get_leave_type(leave_type_id)

    def list_leave_types(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        is_active: bool | None = None,
    ) -> tuple[list[LeaveType], int]:
        if offset < 0:
            raise ValueError(
                "Offset cannot be negative."
            )

        if limit < 1 or limit > 100:
            raise ValueError(
                "Limit must be between 1 and 100."
            )

        filters: list[Any] = []

        if is_active is not None:
            filters.append(
                LeaveType.is_active.is_(is_active)
            )

        total = self.db.scalar(
            select(func.count(LeaveType.id)).where(*filters)
        ) or 0

        statement = (
            select(LeaveType)
            .where(*filters)
            .order_by(LeaveType.id)
            .offset(offset)
            .limit(limit)
        )

        items = list(
            self.db.scalars(statement).all()
        )

        return items, total

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create_leave_type(
        self,
        *,
        data: LeaveTypeCreate,
        actor_user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LeaveType:
        name = self._normalize_name(data.name)
        code = self._normalize_code(data.code)

        self._ensure_name_available(name=name)
        self._ensure_code_available(code=code)

        leave_type = LeaveType(
            name=name,
            code=code,
            description=(
                data.description.strip()
                if data.description
                else None
            ),
            default_annual_allowance=Decimal(
                data.default_annual_allowance
            ),
            is_active=data.is_active,
        )

        self.db.add(leave_type)

        try:
            self.db.flush()
        except IntegrityError as exc:
            raise ResourceConflictError(
                "Leave type with the same name or code already exists."
            ) from exc

        self.audit_service.log(
            user_id=actor_user_id,
            action=AuditAction.CREATE_LEAVE_TYPE,
            entity_type="leave_type",
            entity_id=leave_type.id,
            details={
                "name": leave_type.name,
                "code": leave_type.code,
                "default_annual_allowance": str(
                    leave_type.default_annual_allowance
                ),
                "is_active": leave_type.is_active,
            },
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.flush()

        return leave_type

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_leave_type(
        self,
        *,
        leave_type_id: int,
        data: LeaveTypeUpdate,
        actor_user_id: int,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LeaveType:
        leave_type = self._get_leave_type(leave_type_id)

        changes: dict[str, Any] = {}

        if data.name is not None:
            name = self._normalize_name(data.name)

            if name.lower() != leave_type.name.lower():
                self._ensure_name_available(
                    name=name,
                    exclude_id=leave_type.id,
                )

                changes["name"] = {
                    "from": leave_type.name,
                    "to": name,
                }

                leave_type.name = name

        if data.description is not None:
            description = data.description.strip() or None

            if description != leave_type.description:
                changes["description"] = {
                    "from": leave_type.description,
                    "to": description,
                }

                leave_type.description = description

        if data.default_annual_allowance is not None:
            allowance = Decimal(
                data.default_annual_allowance
            )

            if allowance != leave_type.default_annual_allowance:
                changes["default_annual_allowance"] = {
                    "from": str(
                        leave_type.default_annual_allowance
                    ),
                    "to": str(allowance),
                }

                leave_type.default_annual_allowance = allowance

        if data.is_active is not None:
            if data.is_active != leave_type.is_active:
                changes["is_active"] = {
                    "from": leave_type.is_active,
                    "to": data.is_active,
                }

                leave_type.is_active = data.is_active

        if changes:
            self.audit_service.log(
                user_id=actor_user_id,
                action=AuditAction.UPDATE_LEAVE_TYPE,
                entity_type="leave_type",
                entity_id=leave_type.id,
                details=changes,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        self.db.flush()

        return leave_type