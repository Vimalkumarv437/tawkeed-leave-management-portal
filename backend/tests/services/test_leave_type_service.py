from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.enums import AuditAction, Role
from app.core.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.leave_type import LeaveType
from app.models.user import User
from app.schemas.leave_type import LeaveTypeCreate, LeaveTypeUpdate
from app.services.leave_type_service import LeaveTypeService


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def create_admin(db) -> User:
    admin = User(
        first_name="Admin",
        last_name="Tester",
        email=f"{unique_value('admin')}@example.com",
        password_hash=hash_password("StrongPassword123!"),
        role=Role.ADMIN,
        is_active=True,
    )

    db.add(admin)
    db.flush()

    return admin


def create_leave_type(
    db,
    *,
    name: str | None = None,
    code: str | None = None,
    allowance: Decimal = Decimal("20.00"),
    is_active: bool = True,
) -> LeaveType:
    leave_type = LeaveType(
        name=name or unique_value("Leave"),
        code=(code or unique_value("CODE")).upper(),
        description="Test leave type",
        default_annual_allowance=allowance,
        is_active=is_active,
    )

    db.add(leave_type)
    db.flush()

    return leave_type


def create_leave_type_data(
    *,
    name: str | None = None,
    code: str | None = None,
    allowance: Decimal = Decimal("20.00"),
    is_active: bool = True,
) -> LeaveTypeCreate:
    return LeaveTypeCreate(
        name=name or unique_value("Annual Leave"),
        code=code or unique_value("ANNUAL"),
        description="Test leave",
        default_annual_allowance=allowance,
        is_active=is_active,
    )


# -------------------------------------------------------------------
# Get
# -------------------------------------------------------------------


def test_get_leave_type_returns_existing_leave_type(db):
    leave_type = create_leave_type(db)

    service = LeaveTypeService(db)

    result = service.get_leave_type(
        leave_type_id=leave_type.id,
    )

    assert result.id == leave_type.id
    assert result.name == leave_type.name
    assert result.code == leave_type.code


def test_get_missing_leave_type_raises_error(db):
    service = LeaveTypeService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave type not found.",
    ):
        service.get_leave_type(
            leave_type_id=999999,
        )


# -------------------------------------------------------------------
# List
# -------------------------------------------------------------------


def test_list_leave_types_returns_items_and_total(db):
    first = create_leave_type(db)
    second = create_leave_type(db)

    service = LeaveTypeService(db)

    items, total = service.list_leave_types(
        offset=0,
        limit=100,
    )

    ids = {item.id for item in items}

    assert total >= 2
    assert first.id in ids
    assert second.id in ids


def test_list_leave_types_filters_active_status(db):
    active = create_leave_type(
        db,
        is_active=True,
    )

    inactive = create_leave_type(
        db,
        is_active=False,
    )

    service = LeaveTypeService(db)

    items, total = service.list_leave_types(
        is_active=True,
        offset=0,
        limit=100,
    )

    ids = {item.id for item in items}

    assert total >= 1
    assert active.id in ids
    assert inactive.id not in ids

    assert all(
        item.is_active is True
        for item in items
    )


def test_list_leave_types_supports_pagination(db):
    create_leave_type(db)
    create_leave_type(db)
    create_leave_type(db)

    service = LeaveTypeService(db)

    items, total = service.list_leave_types(
        offset=1,
        limit=2,
    )

    assert total >= 3
    assert len(items) <= 2


def test_list_leave_types_rejects_negative_offset(db):
    service = LeaveTypeService(db)

    with pytest.raises(
        ValueError,
        match="Offset cannot be negative.",
    ):
        service.list_leave_types(
            offset=-1,
        )


def test_list_leave_types_rejects_invalid_limit(db):
    service = LeaveTypeService(db)

    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100.",
    ):
        service.list_leave_types(
            limit=101,
        )


# -------------------------------------------------------------------
# Create
# -------------------------------------------------------------------


def test_create_leave_type(db):
    admin = create_admin(db)

    data = create_leave_type_data(
        name=unique_value("Annual Leave"),
        code=unique_value("ANNUAL"),
        allowance=Decimal("20.00"),
    )

    service = LeaveTypeService(db)

    result = service.create_leave_type(
        data=data,
        actor_user_id=admin.id,
    )

    assert result.id is not None
    assert result.name == data.name
    assert result.code == data.code.upper()
    assert result.default_annual_allowance == Decimal("20.00")
    assert result.is_active is True


def test_create_leave_type_trims_name(db):
    admin = create_admin(db)

    base_name = unique_value("Annual Leave")

    data = create_leave_type_data(
        name=f"  {base_name}  ",
        code=unique_value("ANNUAL"),
    )

    service = LeaveTypeService(db)

    result = service.create_leave_type(
        data=data,
        actor_user_id=admin.id,
    )

    assert result.name == base_name

def test_create_leave_type_normalizes_code_to_uppercase(db):
    admin = create_admin(db)

    data = create_leave_type_data(
        name="Casual Leave",
        code="casual",
    )

    service = LeaveTypeService(db)

    result = service.create_leave_type(
        data=data,
        actor_user_id=admin.id,
    )

    assert result.code == "CASUAL"


def test_duplicate_leave_type_name_is_rejected(db):
    admin = create_admin(db)

    existing_name = unique_value("Annual Leave")

    create_leave_type(
        db,
        name=existing_name,
        code=unique_value("ANNUAL"),
    )

    data = create_leave_type_data(
        name=existing_name,
        code=unique_value("ANNUAL"),
    )

    service = LeaveTypeService(db)

    with pytest.raises(
        ResourceConflictError,
        match="name already exists",
    ):
        service.create_leave_type(
            data=data,
            actor_user_id=admin.id,
        )

def test_duplicate_leave_type_code_is_rejected(db):
    admin = create_admin(db)

    existing_code = unique_value("ANNUAL").upper()

    create_leave_type(
        db,
        name=unique_value("Annual Leave"),
        code=existing_code,
    )

    data = create_leave_type_data(
        name=unique_value("Annual Leave 2"),
        code=existing_code,
    )

    service = LeaveTypeService(db)

    with pytest.raises(
        ResourceConflictError,
        match="code already exists",
    ):
        service.create_leave_type(
            data=data,
            actor_user_id=admin.id,
        )

def test_create_leave_type_creates_audit_record(db):
    admin = create_admin(db)

    data = create_leave_type_data(
        name="Audit Leave",
        code="AUDIT",
    )

    service = LeaveTypeService(db)

    result = service.create_leave_type(
        data=data,
        actor_user_id=admin.id,
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.user_id == admin.id,
            AuditLog.action == AuditAction.CREATE_LEAVE_TYPE,
            AuditLog.entity_type == "leave_type",
            AuditLog.entity_id == result.id,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.details is not None
    assert audit.details["name"] == result.name
    assert audit.details["code"] == result.code
    assert audit.details["default_annual_allowance"] == "20.00"


# -------------------------------------------------------------------
# Update
# -------------------------------------------------------------------


def test_update_leave_type_name(db):
    admin = create_admin(db)

    leave_type = create_leave_type(
        db,
        name="Old Name",
        code="OLDNAME",
    )

    data = LeaveTypeUpdate(
        name="New Name",
    )

    service = LeaveTypeService(db)

    result = service.update_leave_type(
        leave_type_id=leave_type.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.name == "New Name"
    assert result.code == "OLDNAME"


def test_update_leave_type_description(db):
    admin = create_admin(db)

    leave_type = create_leave_type(
        db,
        name="Description Leave",
        code="DESCRIPTION",
    )

    data = LeaveTypeUpdate(
        description="Updated description",
    )

    service = LeaveTypeService(db)

    result = service.update_leave_type(
        leave_type_id=leave_type.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.description == "Updated description"


def test_update_leave_type_allowance(db):
    admin = create_admin(db)

    leave_type = create_leave_type(
        db,
        allowance=Decimal("20.00"),
    )

    data = LeaveTypeUpdate(
        default_annual_allowance=Decimal("25.00"),
    )

    service = LeaveTypeService(db)

    result = service.update_leave_type(
        leave_type_id=leave_type.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.default_annual_allowance == Decimal("25.00")


def test_update_leave_type_active_status(db):
    admin = create_admin(db)

    leave_type = create_leave_type(
        db,
        is_active=True,
    )

    data = LeaveTypeUpdate(
        is_active=False,
    )

    service = LeaveTypeService(db)

    result = service.update_leave_type(
        leave_type_id=leave_type.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.is_active is False


def test_update_leave_type_does_not_change_code(db):
    admin = create_admin(db)

    leave_type = create_leave_type(
        db,
        code="STABLECODE",
    )

    data = LeaveTypeUpdate(
        name="Updated Name",
    )

    service = LeaveTypeService(db)

    result = service.update_leave_type(
        leave_type_id=leave_type.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.code == "STABLECODE"


def test_update_leave_type_duplicate_name_is_rejected(db):
    admin = create_admin(db)

    existing_name = unique_value("Annual Leave")

    create_leave_type(
        db,
        name=existing_name,
        code=unique_value("ANNUAL"),
    )

    other = create_leave_type(
        db,
        name=unique_value("Other Leave"),
        code=unique_value("OTHER"),
    )

    data = LeaveTypeUpdate(
        name=existing_name,
    )

    service = LeaveTypeService(db)

    with pytest.raises(
        ResourceConflictError,
        match="name already exists",
    ):
        service.update_leave_type(
            leave_type_id=other.id,
            data=data,
            actor_user_id=admin.id,
        )

def test_update_leave_type_same_name_case_insensitively_is_allowed(db):
    admin = create_admin(db)

    original_name = unique_value("Annual Leave")

    leave_type = create_leave_type(
        db,
        name=original_name,
        code=unique_value("ANNUAL"),
    )

    data = LeaveTypeUpdate(
        name=original_name.lower(),
    )

    service = LeaveTypeService(db)

    result = service.update_leave_type(
        leave_type_id=leave_type.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.name == original_name
    assert result.code == leave_type.code
def test_update_missing_leave_type_raises_error(db):
    admin = create_admin(db)

    service = LeaveTypeService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="Leave type not found.",
    ):
        service.update_leave_type(
            leave_type_id=999999,
            data=LeaveTypeUpdate(
                name="Updated",
            ),
            actor_user_id=admin.id,
        )


def test_update_leave_type_creates_audit_record(db):
    admin = create_admin(db)

    leave_type = create_leave_type(
        db,
        name="Old Name",
        code="OLD",
    )

    service = LeaveTypeService(db)

    service.update_leave_type(
        leave_type_id=leave_type.id,
        data=LeaveTypeUpdate(
            name="New Name",
            default_annual_allowance=Decimal("25.00"),
        ),
        actor_user_id=admin.id,
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.user_id == admin.id,
            AuditLog.action == AuditAction.UPDATE_LEAVE_TYPE,
            AuditLog.entity_type == "leave_type",
            AuditLog.entity_id == leave_type.id,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.details is not None
    assert "name" in audit.details
    assert "default_annual_allowance" in audit.details