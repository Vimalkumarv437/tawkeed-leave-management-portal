from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.enums import LeaveStatus, Role
from app.core.security import create_access_token, hash_password
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.user import User
from app.services.leave_service import LeaveService


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:10]}@example.com"


def create_user(
    db,
    *,
    role: Role,
    manager_id: int | None = None,
) -> User:
    user = User(
        first_name="Manager",
        last_name="Test",
        email=unique_email(role.value.lower()),
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


def create_leave_type(db) -> LeaveType:
    leave_type = LeaveType(
        name=f"Annual {uuid4().hex[:8]}",
        code=f"ANNUAL{uuid4().hex[:6].upper()}",
        description="Annual leave",
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


def create_pending_leave(
    db,
    *,
    employee: User,
    leave_type: LeaveType,
    start_date: date | None = None,
):
    start = start_date or future_weekday()

    service = LeaveService(db)

    return service.create_leave_request(
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=start,
        end_date=start,
        reason="Manager API test",
    )


# -------------------------------------------------------------------
# Team requests
# -------------------------------------------------------------------


def test_manager_can_view_own_team_requests(
    client: TestClient,
    db,
):
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

    request = create_pending_leave(
        db,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
    )

    response = client.get(
        "/api/manager/requests",
        headers=auth_headers(manager),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == request.id
    assert data["items"][0]["user_id"] == employee.id
    assert data["items"][0]["status"] == LeaveStatus.PENDING.value


def test_manager_cannot_see_another_team_requests(
    client: TestClient,
    db,
):
    manager1 = create_manager(db)
    manager2 = create_manager(db)

    employee2 = create_employee(
        db,
        manager=manager2,
    )

    leave_type = create_leave_type(db)
    start = future_weekday()

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type,
        year=start.year,
    )

    request = create_pending_leave(
        db,
        employee=employee2,
        leave_type=leave_type,
        start_date=start,
    )

    response = client.get(
        "/api/manager/requests",
        headers=auth_headers(manager1),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 0
    assert not any(
        item["id"] == request.id
        for item in data["items"]
    )


def test_manager_can_filter_team_requests_by_status(
    client: TestClient,
    db,
):
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

    request = create_pending_leave(
        db,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
    )

    response = client.get(
        "/api/manager/requests?status=PENDING",
        headers=auth_headers(manager),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["id"] == request.id
    assert data["items"][0]["status"] == "PENDING"


# -------------------------------------------------------------------
# Approval
# -------------------------------------------------------------------


def test_manager_can_approve_own_team_request(
    client: TestClient,
    db,
):
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

    request = create_pending_leave(
        db,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
    )

    response = client.post(
        f"/api/manager/requests/{request.id}/approve",
        headers=auth_headers(manager),
        json={
            "comment": "Approved by manager.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == request.id
    assert data["status"] == LeaveStatus.APPROVED.value
    assert data["approved_by_id"] == manager.id
    assert data["approval_comment"] == "Approved by manager."
    assert data["approved_at"] is not None


def test_manager_cannot_approve_another_team_request(
    client: TestClient,
    db,
):
    manager1 = create_manager(db)
    manager2 = create_manager(db)

    employee2 = create_employee(
        db,
        manager=manager2,
    )

    leave_type = create_leave_type(db)
    start = future_weekday()

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type,
        year=start.year,
    )

    request = create_pending_leave(
        db,
        employee=employee2,
        leave_type=leave_type,
        start_date=start,
    )

    response = client.post(
        f"/api/manager/requests/{request.id}/approve",
        headers=auth_headers(manager1),
        json={
            "comment": "Should fail.",
        },
    )

    assert response.status_code == 403


def test_manager_cannot_approve_same_request_twice(
    client: TestClient,
    db,
):
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

    request = create_pending_leave(
        db,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
    )

    first_response = client.post(
        f"/api/manager/requests/{request.id}/approve",
        headers=auth_headers(manager),
        json={
            "comment": "Approved.",
        },
    )

    assert first_response.status_code == 200

    second_response = client.post(
        f"/api/manager/requests/{request.id}/approve",
        headers=auth_headers(manager),
        json={
            "comment": "Approve again.",
        },
    )

    assert second_response.status_code == 409


# -------------------------------------------------------------------
# Rejection
# -------------------------------------------------------------------


def test_manager_can_reject_own_team_request(
    client: TestClient,
    db,
):
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

    request = create_pending_leave(
        db,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
    )

    response = client.post(
        f"/api/manager/requests/{request.id}/reject",
        headers=auth_headers(manager),
        json={
            "comment": "Rejected due to staffing.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == request.id
    assert data["status"] == LeaveStatus.REJECTED.value
    assert data["approval_comment"] == "Rejected due to staffing."


def test_manager_cannot_reject_another_team_request(
    client: TestClient,
    db,
):
    manager1 = create_manager(db)
    manager2 = create_manager(db)

    employee2 = create_employee(
        db,
        manager=manager2,
    )

    leave_type = create_leave_type(db)
    start = future_weekday()

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type,
        year=start.year,
    )

    request = create_pending_leave(
        db,
        employee=employee2,
        leave_type=leave_type,
        start_date=start,
    )

    response = client.post(
        f"/api/manager/requests/{request.id}/reject",
        headers=auth_headers(manager1),
        json={
            "comment": "Should fail.",
        },
    )

    assert response.status_code == 403


# -------------------------------------------------------------------
# Team calendar
# -------------------------------------------------------------------


def test_manager_calendar_returns_approved_team_leave(
    client: TestClient,
    db,
):
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

    request = create_pending_leave(
        db,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
    )

    approve_response = client.post(
        f"/api/manager/requests/{request.id}/approve",
        headers=auth_headers(manager),
        json={
            "comment": "Approved for calendar test.",
        },
    )

    assert approve_response.status_code == 200

    response = client.get(
        "/api/manager/calendar",
        headers=auth_headers(manager),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == request.id
    assert data["items"][0]["status"] == LeaveStatus.APPROVED.value


def test_manager_calendar_excludes_pending_and_rejected_leave(
    client: TestClient,
    db,
):
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

    pending_request = create_pending_leave(
        db,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
    )

    reject_response = client.post(
        f"/api/manager/requests/{pending_request.id}/reject",
        headers=auth_headers(manager),
        json={
            "comment": "Rejected.",
        },
    )

    assert reject_response.status_code == 200

    response = client.get(
        "/api/manager/calendar",
        headers=auth_headers(manager),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []


# -------------------------------------------------------------------
# Authorization
# -------------------------------------------------------------------


def test_employee_cannot_access_manager_requests(
    client: TestClient,
    db,
):
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )

    response = client.get(
        "/api/manager/requests",
        headers=auth_headers(employee),
    )

    assert response.status_code == 403


def test_employee_cannot_approve_manager_request(
    client: TestClient,
    db,
):
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

    request = create_pending_leave(
        db,
        employee=employee,
        leave_type=leave_type,
        start_date=start,
    )

    response = client.post(
        f"/api/manager/requests/{request.id}/approve",
        headers=auth_headers(employee),
        json={
            "comment": "Should not work.",
        },
    )

    assert response.status_code == 403


def test_employee_cannot_access_manager_calendar(
    client: TestClient,
    db,
):
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )

    response = client.get(
        "/api/manager/calendar",
        headers=auth_headers(employee),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_access_manager_requests(
    client: TestClient,
):
    response = client.get(
        "/api/manager/requests",
    )

    assert response.status_code == 401

def test_manager_can_cancel_own_leave(
    client: TestClient,
    db,
):
    manager = create_manager(db)
    leave_type = create_leave_type(db)
    start = future_weekday()

    create_balance(
        db,
        employee=manager,
        leave_type=leave_type,
        year=start.year,
        allocated=Decimal("10.00"),
    )

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(manager),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    response = client.post(
        f"/api/leaves/{request_id}/cancel",
        headers=auth_headers(manager),
    )

    assert response.status_code == 200
    assert response.json()["status"] == LeaveStatus.CANCELLED.value