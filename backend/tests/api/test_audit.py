from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.enums import AuditAction, LeaveStatus, Role
from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditLog
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.user import User


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def create_user(
    db,
    *,
    role: Role,
    manager_id: int | None = None,
) -> User:
    user = User(
        first_name="Audit",
        last_name="Tester",
        email=f"{unique_value('audit_user')}@example.com",
        password_hash=hash_password("StrongPassword123!"),
        role=role,
        manager_id=manager_id,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_manager(db) -> User:
    return create_user(
        db,
        role=Role.MANAGER,
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
    )


def create_admin(db) -> User:
    return create_user(
        db,
        role=Role.ADMIN,
    )


def create_leave_type(db) -> LeaveType:
    leave_type = LeaveType(
        name=unique_value("Audit Leave"),
        code=unique_value("AUDIT").upper(),
        description="Audit API test leave type",
        default_annual_allowance=Decimal("20.00"),
        is_active=True,
    )

    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)

    return leave_type


def create_balance(
    db,
    *,
    employee: User,
    leave_type: LeaveType,
    year: int,
    allocated: Decimal = Decimal("20.00"),
) -> LeaveBalance:
    balance = LeaveBalance(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=year,
        allocated_days=allocated,
        used_days=Decimal("0.00"),
        reserved_days=Decimal("0.00"),
    )

    db.add(balance)
    db.commit()
    db.refresh(balance)

    return balance


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        token_version=user.token_version,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def future_weekday(days_ahead: int = 7) -> date:
    result = date.today() + timedelta(days=days_ahead)

    while result.weekday() >= 5:
        result += timedelta(days=1)

    return result


def create_leave_setup(db):
    manager = create_manager(db)

    employee = create_employee(
        db,
        manager=manager,
    )

    leave_type = create_leave_type(db)
    start = future_weekday()

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=start.year,
    )

    return manager, employee, leave_type, start


def get_audit_logs(
    db,
    *,
    action: AuditAction | None = None,
    entity_id: int | None = None,
) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(
        AuditLog.id.desc()
    )

    if action is not None:
        stmt = stmt.where(
            AuditLog.action == action
        )

    if entity_id is not None:
        stmt = stmt.where(
            AuditLog.entity_id == entity_id
        )

    return list(db.scalars(stmt).all())


# -------------------------------------------------------------------
# Authorization
# -------------------------------------------------------------------


def test_admin_can_view_audit_logs(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    response = client.get(
        "/api/admin/audit-logs",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert "items" in data
    assert "total" in data
    assert "offset" in data
    assert "limit" in data


def test_employee_cannot_view_audit_logs(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    response = client.get(
        "/api/admin/audit-logs",
        headers=auth_headers(employee),
    )

    assert response.status_code == 403


def test_manager_cannot_view_audit_logs(
    client: TestClient,
    db,
):
    manager = create_manager(db)

    response = client.get(
        "/api/admin/audit-logs",
        headers=auth_headers(manager),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_view_audit_logs(
    client: TestClient,
):
    response = client.get(
        "/api/admin/audit-logs",
    )

    assert response.status_code == 401


# -------------------------------------------------------------------
# Pagination and filters
# -------------------------------------------------------------------


def test_audit_logs_support_pagination(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    # Create audit records directly so this test isolates
    # pagination behavior from UserService audit generation.
    for _ in range(2):
        db.add(
            AuditLog(
                user_id=admin.id,
                action=AuditAction.CREATE_USER,
                entity_type="user",
                entity_id=admin.id,
                details={
                    "test": "pagination",
                },
            )
        )

    db.commit()

    response = client.get(
        "/api/admin/audit-logs?offset=0&limit=1",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["offset"] == 0
    assert data["limit"] == 1
    assert len(data["items"]) == 1
    assert data["total"] >= 2

def test_audit_logs_can_filter_by_action(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    manager = create_manager(db)

    response = client.get(
        "/api/admin/audit-logs"
        f"?action={AuditAction.CREATE_USER.value}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["action"] == AuditAction.CREATE_USER.value
        for item in data["items"]
    )


def test_audit_logs_can_filter_by_user_id(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    manager = create_manager(db)

    response = client.get(
        f"/api/admin/audit-logs?user_id={manager.id}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["user_id"] == manager.id
        for item in data["items"]
    )


def test_invalid_audit_pagination_is_rejected(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    response = client.get(
        "/api/admin/audit-logs?limit=101",
        headers=auth_headers(admin),
    )

    assert response.status_code == 422


# -------------------------------------------------------------------
# Required leave audit trail
# -------------------------------------------------------------------


def test_leave_creation_creates_audit_log(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_leave_setup(db)

    response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
            "reason": "Audit create test",
        },
    )

    assert response.status_code == 201

    request_id = response.json()["id"]

    logs = get_audit_logs(
        db,
        action=AuditAction.CREATE_LEAVE,
        entity_id=request_id,
    )

    assert len(logs) >= 1

    log = logs[0]

    assert log.user_id == employee.id
    assert log.entity_type == "leave_request"
    assert log.entity_id == request_id
    assert log.action == AuditAction.CREATE_LEAVE


def test_approval_creates_audit_log(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_leave_setup(db)

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    approve_response = client.post(
        f"/api/manager/requests/{request_id}/approve",
        headers=auth_headers(manager),
        json={
            "comment": "Approved for audit test.",
        },
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == (
        LeaveStatus.APPROVED.value
    )

    logs = get_audit_logs(
        db,
        action=AuditAction.APPROVE_LEAVE,
        entity_id=request_id,
    )

    assert len(logs) >= 1

    log = logs[0]

    assert log.user_id == manager.id
    assert log.entity_type == "leave_request"
    assert log.entity_id == request_id
    assert log.action == AuditAction.APPROVE_LEAVE


def test_rejection_creates_audit_log(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_leave_setup(db)

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    reject_response = client.post(
        f"/api/manager/requests/{request_id}/reject",
        headers=auth_headers(manager),
        json={
            "comment": "Rejected for audit test.",
        },
    )

    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == (
        LeaveStatus.REJECTED.value
    )

    logs = get_audit_logs(
        db,
        action=AuditAction.REJECT_LEAVE,
        entity_id=request_id,
    )

    assert len(logs) >= 1

    log = logs[0]

    assert log.user_id == manager.id
    assert log.entity_type == "leave_request"
    assert log.entity_id == request_id
    assert log.action == AuditAction.REJECT_LEAVE


def test_cancellation_creates_audit_log(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_leave_setup(db)

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    cancel_response = client.post(
        f"/api/leaves/{request_id}/cancel",
        headers=auth_headers(employee),
        json={
            "reason": "No longer needed.",
        },
    )

    assert cancel_response.status_code == 200
    assert cancel_response.json()["status"] == (
        LeaveStatus.CANCELLED.value
    )

    logs = get_audit_logs(
        db,
        action=AuditAction.CANCEL_LEAVE,
        entity_id=request_id,
    )

    assert len(logs) >= 1

    log = logs[0]

    assert log.user_id == employee.id
    assert log.entity_type == "leave_request"
    assert log.entity_id == request_id
    assert log.action == AuditAction.CANCEL_LEAVE