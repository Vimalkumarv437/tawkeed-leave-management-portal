from __future__ import annotations

from decimal import Decimal
from uuid import uuid4
from types import SimpleNamespace
import pytest
from sqlalchemy import select

from app.core.enums import AuditAction, Role
from app.core.exceptions import (
    AuthorizationError,
    InvalidManagerError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.security import verify_password
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def unique_email(prefix: str = "user-service") -> str:
    return f"{prefix}-{uuid4().hex[:10]}@example.com"


def create_user(
    db,
    *,
    role: Role,
    manager_id: int | None = None,
    email: str | None = None,
    is_active: bool = True,
) -> User:
    user = User(
        first_name="Existing",
        last_name="User",
        email=email or unique_email(role.value.lower()),
        password_hash="existing-hash",
        role=role,
        manager_id=manager_id,
        is_active=is_active,
    )

    db.add(user)
    db.flush()

    return user


def create_admin(db) -> User:
    return create_user(
        db,
        role=Role.ADMIN,
        email=unique_email("admin"),
    )


def create_manager(db) -> User:
    return create_user(
        db,
        role=Role.MANAGER,
        email=unique_email("manager"),
    )


def create_employee(
    db,
    *,
    manager: User,
) -> User:
    return create_user(
        db,
        role=Role.EMPLOYEE,
        manager_id=manager.id,
        email=unique_email("employee"),
    )


def employee_create_data(
    *,
    manager_id: int,
) -> UserCreate:
    return UserCreate(
        first_name="New",
        last_name="Employee",
        email=unique_email("new-employee"),
        password="StrongPassword123!",
        role=Role.EMPLOYEE,
        manager_id=manager_id,
    )


def manager_create_data() -> UserCreate:
    return UserCreate(
        first_name="New",
        last_name="Manager",
        email=unique_email("new-manager"),
        password="StrongPassword123!",
        role=Role.MANAGER,
    )


# -------------------------------------------------------------------
# Get user
# -------------------------------------------------------------------


def test_get_user_returns_existing_user(db):
    user = create_employee(
        db,
        manager=create_manager(db),
    )

    service = UserService(db)

    result = service.get_user(
        user_id=user.id,
    )

    assert result.id == user.id
    assert result.email == user.email


def test_get_user_missing_user_raises_error(db):
    service = UserService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="User not found.",
    ):
        service.get_user(
            user_id=999999,
        )


# -------------------------------------------------------------------
# List users
# -------------------------------------------------------------------


def test_list_users_returns_users_and_total(db):
    admin = create_admin(db)
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )

    service = UserService(db)

    _, total = service.list_users()

    assert total >= 3

    # Fetch the final page so the users created by this test
    # are included even when previous tests have populated the DB.
    offset = max(total - 100, 0)

    users, page_total = service.list_users(
        offset=offset,
        limit=100,
    )

    ids = {user.id for user in users}

    assert page_total == total
    assert admin.id in ids
    assert manager.id in ids
    assert employee.id in ids

def test_list_users_filters_by_role(db):
    manager = create_manager(db)

    employee = create_employee(
        db,
        manager=manager,
    )

    service = UserService(db)

    _, total = service.list_users(
        role=Role.EMPLOYEE,
    )

    offset = max(total - 100, 0)

    users, page_total = service.list_users(
        role=Role.EMPLOYEE,
        offset=offset,
        limit=100,
    )

    ids = {user.id for user in users}

    assert page_total == total
    assert employee.id in ids

    assert all(
        user.role == Role.EMPLOYEE
        for user in users
    )


def test_list_users_filters_by_active_status(db):
    active_user = create_user(
        db,
        role=Role.MANAGER,
        is_active=True,
    )

    inactive_user = create_user(
        db,
        role=Role.MANAGER,
        is_active=False,
    )

    service = UserService(db)

    _, total = service.list_users(
        is_active=True,
    )

    offset = max(total - 100, 0)

    users, page_total = service.list_users(
        is_active=True,
        offset=offset,
        limit=100,
    )

    ids = {user.id for user in users}

    assert page_total == total
    assert active_user.id in ids
    assert inactive_user.id not in ids

    assert all(
        user.is_active is True
        for user in users
    )


def test_list_users_pagination(db):
    for _ in range(3):
        create_user(
            db,
            role=Role.MANAGER,
        )

    service = UserService(db)

    users, total = service.list_users(
        offset=1,
        limit=2,
    )

    assert total >= 3
    assert len(users) <= 2


def test_list_users_rejects_negative_offset(db):
    service = UserService(db)

    with pytest.raises(
        ValueError,
        match="Offset cannot be negative.",
    ):
        service.list_users(
            offset=-1,
        )


def test_list_users_rejects_invalid_limit(db):
    service = UserService(db)

    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100.",
    ):
        service.list_users(
            limit=101,
        )


# -------------------------------------------------------------------
# Create users
# -------------------------------------------------------------------


def test_create_employee_with_valid_manager(db):
    admin = create_admin(db)
    manager = create_manager(db)

    data = employee_create_data(
        manager_id=manager.id,
    )

    service = UserService(db)

    user = service.create_user(
        data=data,
        actor_user_id=admin.id,
    )

    assert user.id is not None
    assert user.first_name == "New"
    assert user.last_name == "Employee"
    assert user.role == Role.EMPLOYEE
    assert user.manager_id == manager.id
    assert user.is_active is True
    assert user.email == data.email.lower()

    assert verify_password(
        data.password,
        user.password_hash,
    )


def test_create_manager_without_manager_is_valid(db):
    admin = create_admin(db)

    data = manager_create_data()

    service = UserService(db)

    user = service.create_user(
        data=data,
        actor_user_id=admin.id,
    )

    assert user.role == Role.MANAGER
    assert user.manager_id is None


def test_employee_without_manager_is_rejected(db):
    admin = create_admin(db)

    data = SimpleNamespace(
        first_name="No",
        last_name="Manager",
        email=unique_email("no-manager"),
        password="StrongPassword123!",
        role=Role.EMPLOYEE,
        manager_id=None,
    )

    service = UserService(db)

    with pytest.raises(
        InvalidManagerError,
        match="Employees must have a manager.",
    ):
        service.create_user(
            data=data,
            actor_user_id=admin.id,
        )


def test_non_employee_cannot_have_manager(db):
    admin = create_admin(db)
    manager = create_manager(db)

    data = SimpleNamespace(
        first_name="Invalid",
        last_name="Manager",
        email=unique_email("invalid-manager"),
        password="StrongPassword123!",
        role=Role.MANAGER,
        manager_id=manager.id,
    )

    service = UserService(db)

    with pytest.raises(
        InvalidManagerError,
        match="Only employees can be assigned a manager.",
    ):
        service.create_user(
            data=data,
            actor_user_id=admin.id,
        )

def test_invalid_manager_id_is_rejected(db):
    admin = create_admin(db)

    data = employee_create_data(
        manager_id=999999,
    )

    service = UserService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="User not found.",
    ):
        service.create_user(
            data=data,
            actor_user_id=admin.id,
        )


def test_employee_manager_must_have_manager_role(db):
    admin = create_admin(db)
    non_manager = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    data = employee_create_data(
        manager_id=non_manager.id,
    )

    service = UserService(db)

    with pytest.raises(
        InvalidManagerError,
        match="assigned manager must have MANAGER role",
    ):
        service.create_user(
            data=data,
            actor_user_id=admin.id,
        )


def test_inactive_manager_cannot_be_assigned(db):
    admin = create_admin(db)

    inactive_manager = create_manager(db)
    inactive_manager.is_active = False
    db.flush()

    data = employee_create_data(
        manager_id=inactive_manager.id,
    )

    service = UserService(db)

    with pytest.raises(
        InvalidManagerError,
        match="assigned manager is inactive",
    ):
        service.create_user(
            data=data,
            actor_user_id=admin.id,
        )


def test_duplicate_email_is_rejected(db):
    admin = create_admin(db)
    manager = create_manager(db)

    existing = create_employee(
        db,
        manager=manager,
    )

    data = UserCreate(
        first_name="Duplicate",
        last_name="Email",
        email=existing.email.upper(),
        password="StrongPassword123!",
        role=Role.EMPLOYEE,
        manager_id=manager.id,
    )

    service = UserService(db)

    with pytest.raises(
        ResourceConflictError,
        match="user with this email already exists",
    ):
        service.create_user(
            data=data,
            actor_user_id=admin.id,
        )


def test_created_user_generates_create_user_audit(db):
    admin = create_admin(db)
    manager = create_manager(db)

    data = employee_create_data(
        manager_id=manager.id,
    )

    service = UserService(db)

    user = service.create_user(
        data=data,
        actor_user_id=admin.id,
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.user_id == admin.id,
            AuditLog.action == AuditAction.CREATE_USER,
            AuditLog.entity_type == "user",
            AuditLog.entity_id == user.id,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.details is not None
    assert audit.details["email"] == user.email
    assert audit.details["role"] == Role.EMPLOYEE.value
    assert audit.details["manager_id"] == manager.id


# -------------------------------------------------------------------
# Update users
# -------------------------------------------------------------------


def test_update_user_names(db):
    admin = create_admin(db)
    manager = create_manager(db)

    employee = create_employee(
        db,
        manager=manager,
    )

    data = UserUpdate(
        first_name="UpdatedFirst",
        last_name="UpdatedLast",
    )

    service = UserService(db)

    result = service.update_user(
        user_id=employee.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.first_name == "UpdatedFirst"
    assert result.last_name == "UpdatedLast"


def test_update_user_email_normalizes_to_lowercase(db):
    admin = create_admin(db)
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )

    new_email = unique_email("updated-email").upper()

    data = UserUpdate(
        email=new_email,
    )

    service = UserService(db)

    result = service.update_user(
        user_id=employee.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.email == new_email.lower()


def test_update_user_rejects_duplicate_email(db):
    admin = create_admin(db)
    manager = create_manager(db)

    employee1 = create_employee(
        db,
        manager=manager,
    )

    employee2 = create_employee(
        db,
        manager=manager,
    )

    data = UserUpdate(
        email=employee2.email,
    )

    service = UserService(db)

    with pytest.raises(
        ResourceConflictError,
        match="user with this email already exists",
    ):
        service.update_user(
            user_id=employee1.id,
            data=data,
            actor_user_id=admin.id,
        )


def test_update_employee_manager(db):
    admin = create_admin(db)
    manager1 = create_manager(db)
    manager2 = create_manager(db)

    employee = create_employee(
        db,
        manager=manager1,
    )

    data = UserUpdate(
        manager_id=manager2.id,
    )

    service = UserService(db)

    result = service.update_user(
        user_id=employee.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.manager_id == manager2.id


def test_update_employee_to_self_as_manager_is_rejected(db):
    admin = create_admin(db)
    manager = create_manager(db)

    employee = create_employee(
        db,
        manager=manager,
    )

    data = UserUpdate(
        manager_id=employee.id,
    )

    service = UserService(db)

    with pytest.raises(
        InvalidManagerError,
        match="own manager",
    ):
        service.update_user(
            user_id=employee.id,
            data=data,
            actor_user_id=admin.id,
        )


def test_update_employee_with_non_manager_is_rejected(db):
    admin = create_admin(db)
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )

    other_employee = create_employee(
        db,
        manager=manager,
    )

    data = UserUpdate(
        manager_id=other_employee.id,
    )

    service = UserService(db)

    with pytest.raises(
        InvalidManagerError,
        match="assigned manager must have MANAGER role",
    ):
        service.update_user(
            user_id=employee.id,
            data=data,
            actor_user_id=admin.id,
        )


def test_update_user_can_deactivate(db):
    admin = create_admin(db)
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )

    data = UserUpdate(
        is_active=False,
    )

    service = UserService(db)

    result = service.update_user(
        user_id=employee.id,
        data=data,
        actor_user_id=admin.id,
    )

    assert result.is_active is False


def test_update_user_generates_audit(db):
    admin = create_admin(db)
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )

    data = UserUpdate(
        first_name="Audited",
    )

    service = UserService(db)

    service.update_user(
        user_id=employee.id,
        data=data,
        actor_user_id=admin.id,
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.user_id == admin.id,
            AuditLog.action == AuditAction.UPDATE_USER,
            AuditLog.entity_type == "user",
            AuditLog.entity_id == employee.id,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.details is not None
    assert audit.details["first_name"] == "Audited"


def test_update_missing_user_raises_error(db):
    admin = create_admin(db)

    service = UserService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="User not found.",
    ):
        service.update_user(
            user_id=999999,
            data=UserUpdate(
                first_name="Missing",
            ),
            actor_user_id=admin.id,
        )


# -------------------------------------------------------------------
# Deactivate
# -------------------------------------------------------------------


def test_deactivate_user(db):
    admin = create_admin(db)
    manager = create_manager(db)

    service = UserService(db)

    result = service.deactivate_user(
        user_id=manager.id,
        actor_user_id=admin.id,
    )

    assert result.is_active is False


def test_deactivate_already_inactive_user_is_rejected(db):
    admin = create_admin(db)

    user = create_user(
        db,
        role=Role.MANAGER,
        is_active=False,
    )

    service = UserService(db)

    with pytest.raises(
        ResourceConflictError,
        match="already inactive",
    ):
        service.deactivate_user(
            user_id=user.id,
            actor_user_id=admin.id,
        )


def test_admin_cannot_deactivate_themselves(db):
    admin = create_admin(db)

    service = UserService(db)

    with pytest.raises(
        AuthorizationError,
        match="cannot deactivate their own account",
    ):
        service.deactivate_user(
            user_id=admin.id,
            actor_user_id=admin.id,
        )


def test_deactivate_creates_audit_record(db):
    admin = create_admin(db)
    manager = create_manager(db)

    service = UserService(db)

    service.deactivate_user(
        user_id=manager.id,
        actor_user_id=admin.id,
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.user_id == admin.id,
            AuditLog.action == AuditAction.DEACTIVATE_USER,
            AuditLog.entity_type == "user",
            AuditLog.entity_id == manager.id,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.details is not None
    assert audit.details["email"] == manager.email


def test_deactivate_missing_user_raises_error(db):
    admin = create_admin(db)

    service = UserService(db)

    with pytest.raises(
        ResourceNotFoundError,
        match="User not found.",
    ):
        service.deactivate_user(
            user_id=999999,
            actor_user_id=admin.id,
        )


# -------------------------------------------------------------------
# Reactivate
# -------------------------------------------------------------------


def test_reactivate_inactive_user(db):
    admin = create_admin(db)

    user = create_user(
        db,
        role=Role.MANAGER,
        is_active=False,
    )

    service = UserService(db)

    result = service.reactivate_user(
        user_id=user.id,
        actor_user_id=admin.id,
    )

    assert result.is_active is True


def test_reactivate_already_active_user_is_rejected(db):
    admin = create_admin(db)

    user = create_user(
        db,
        role=Role.MANAGER,
        is_active=True,
    )

    service = UserService(db)

    with pytest.raises(
        ResourceConflictError,
        match="already active",
    ):
        service.reactivate_user(
            user_id=user.id,
            actor_user_id=admin.id,
        )


def test_reactivate_creates_audit_record(db):
    admin = create_admin(db)

    user = create_user(
        db,
        role=Role.MANAGER,
        is_active=False,
    )

    service = UserService(db)

    service.reactivate_user(
        user_id=user.id,
        actor_user_id=admin.id,
    )

    audit = db.scalar(
        select(AuditLog)
        .where(
            AuditLog.user_id == admin.id,
            AuditLog.action == AuditAction.UPDATE_USER,
            AuditLog.entity_type == "user",
            AuditLog.entity_id == user.id,
        )
        .order_by(AuditLog.id.desc())
    )

    assert audit is not None
    assert audit.details is not None
    assert audit.details["is_active"]["from"] is False
    assert audit.details["is_active"]["to"] is True