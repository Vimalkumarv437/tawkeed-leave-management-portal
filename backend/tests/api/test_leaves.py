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


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def unique_holiday_date() -> date:
    return date(2050, 1, 1) + timedelta(
        days=uuid4().int % 10000
    )

def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:10]}"


def create_user(
    db,
    *,
    role: Role,
    manager_id: int | None = None,
) -> User:
    user = User(
        first_name="Leave",
        last_name="Tester",
        email=f"{unique_value('user')}@example.com",
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
        name=unique_value("Annual Leave"),
        code=unique_value("ANNUAL").upper(),
        description="Leave API test type",
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
    used: Decimal = Decimal("0.00"),
    reserved: Decimal = Decimal("0.00"),
) -> LeaveBalance:
    balance = LeaveBalance(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=year,
        allocated_days=allocated,
        used_days=used,
        reserved_days=reserved,
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


def future_saturday(days_ahead: int = 7) -> date:
    result = date.today() + timedelta(days=days_ahead)

    while result.weekday() != 5:
        result += timedelta(days=1)

    return result


def create_employee_setup(
    db,
    *,
    balance: Decimal = Decimal("20.00"),
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
        allocated=balance,
    )

    return manager, employee, leave_type, start


# -------------------------------------------------------------------
# Create leave
# -------------------------------------------------------------------


def test_employee_can_create_leave(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(db)

    response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
            "reason": "Personal work",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == employee.id
    assert data["leave_type_id"] == leave_type.id
    assert data["start_date"] == start.isoformat()
    assert data["end_date"] == start.isoformat()
    assert data["total_days"] == "1.00"
    assert data["status"] == LeaveStatus.PENDING.value
    assert data["reason"] == "Personal work"


def test_manager_can_create_own_leave(
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

    response = client.post(
        "/api/leaves",
        headers=auth_headers(manager),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
            "reason": "Manager leave",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == manager.id
    assert data["status"] == LeaveStatus.PENDING.value


def test_leave_creation_reserves_balance(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
        balance=Decimal("10.00"),
    )

    response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert response.status_code == 201

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.reserved_days == Decimal("1.00")
    assert balance.used_days == Decimal("0.00")
    assert balance.remaining_days == Decimal("9.00")


def test_insufficient_balance_returns_409(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
        balance=Decimal("1.00"),
    )

    response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": (
                start + timedelta(days=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 409


def test_past_leave_date_returns_400(
    client: TestClient,
    db,
):
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )
    leave_type = create_leave_type(db)

    past = date.today() - timedelta(days=1)

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=date.today().year,
    )

    response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": past.isoformat(),
            "end_date": past.isoformat(),
        },
    )

    assert response.status_code == 400


def test_invalid_date_range_returns_400(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(db)

    response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": (
                start - timedelta(days=1)
            ).isoformat(),
        },
    )

    assert response.status_code == 422


def test_weekend_only_leave_returns_400(
    client: TestClient,
    db,
):
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )
    leave_type = create_leave_type(db)

    saturday = future_saturday()

    create_balance(
        db,
        employee=employee,
        leave_type=leave_type,
        year=saturday.year,
        allocated=Decimal("10.00"),
    )

    response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": saturday.isoformat(),
            "end_date": saturday.isoformat(),
        },
    )

    assert response.status_code == 400


def test_overlapping_pending_leave_returns_409(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(db)

    first = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": (
                start + timedelta(days=2)
            ).isoformat(),
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": (
                start + timedelta(days=1)
            ).isoformat(),
            "end_date": (
                start + timedelta(days=3)
            ).isoformat(),
        },
    )

    assert second.status_code == 409


# -------------------------------------------------------------------
# Get leave
# -------------------------------------------------------------------


def test_employee_can_get_own_leave(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(db)

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

    response = client.get(
        f"/api/leaves/{request_id}",
        headers=auth_headers(employee),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == request_id
    assert data["user_id"] == employee.id
    assert data["status"] == LeaveStatus.PENDING.value


def test_employee_cannot_get_another_users_leave(
    client: TestClient,
    db,
):
    manager = create_manager(db)

    employee1 = create_employee(
        db,
        manager=manager,
    )

    employee2 = create_employee(
        db,
        manager=manager,
    )

    leave_type = create_leave_type(db)
    start = future_weekday()

    create_balance(
        db,
        employee=employee1,
        leave_type=leave_type,
        year=start.year,
    )

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type,
        year=start.year,
    )

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee1),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    response = client.get(
        f"/api/leaves/{request_id}",
        headers=auth_headers(employee2),
    )

    assert response.status_code == 403


def test_get_missing_leave_returns_404(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    response = client.get(
        "/api/leaves/999999",
        headers=auth_headers(employee),
    )

    assert response.status_code == 404


# -------------------------------------------------------------------
# Cancellation
# -------------------------------------------------------------------


def test_employee_can_cancel_pending_leave(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
        balance=Decimal("10.00"),
    )

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

    response = client.post(
        f"/api/leaves/{request_id}/cancel",
        headers=auth_headers(employee),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == request_id
    assert data["status"] == LeaveStatus.CANCELLED.value
    assert data["cancelled_by_id"] == employee.id


def test_pending_cancellation_releases_balance(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
        balance=Decimal("10.00"),
    )

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    request_id = create_response.json()["id"]

    response = client.post(
        f"/api/leaves/{request_id}/cancel",
        headers=auth_headers(employee),
    )

    assert response.status_code == 200

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.reserved_days == Decimal("0.00")
    assert balance.used_days == Decimal("0.00")
    assert balance.remaining_days == Decimal("10.00")


def test_employee_can_cancel_approved_leave(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
        balance=Decimal("10.00"),
    )

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
            "comment": "Approved.",
        },
    )

    assert approve_response.status_code == 200

    cancel_response = client.post(
        f"/api/leaves/{request_id}/cancel",
        headers=auth_headers(employee),
    )

    assert cancel_response.status_code == 200

    data = cancel_response.json()

    assert data["status"] == LeaveStatus.CANCELLED.value
    assert data["cancelled_by_id"] == employee.id


def test_approved_cancellation_restores_balance(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
        balance=Decimal("10.00"),
    )

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    request_id = create_response.json()["id"]

    approve_response = client.post(
        f"/api/manager/requests/{request_id}/approve",
        headers=auth_headers(manager),
        json={
            "comment": "Approved.",
        },
    )

    assert approve_response.status_code == 200

    cancel_response = client.post(
        f"/api/leaves/{request_id}/cancel",
        headers=auth_headers(employee),
    )

    assert cancel_response.status_code == 200

    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None
    assert balance.used_days == Decimal("0.00")
    assert balance.reserved_days == Decimal("0.00")
    assert balance.remaining_days == Decimal("10.00")


def test_employee_cannot_cancel_another_users_leave(
    client: TestClient,
    db,
):
    manager = create_manager(db)

    employee1 = create_employee(
        db,
        manager=manager,
    )

    employee2 = create_employee(
        db,
        manager=manager,
    )

    leave_type = create_leave_type(db)
    start = future_weekday()

    create_balance(
        db,
        employee=employee1,
        leave_type=leave_type,
        year=start.year,
    )

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type,
        year=start.year,
    )

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee1),
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
        headers=auth_headers(employee2),
    )

    assert response.status_code == 403


def test_rejected_leave_cannot_be_cancelled(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(db)

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
            "comment": "Rejected.",
        },
    )

    assert reject_response.status_code == 200

    cancel_response = client.post(
        f"/api/leaves/{request_id}/cancel",
        headers=auth_headers(employee),
    )

    assert cancel_response.status_code == 400


# -------------------------------------------------------------------
# Authorization
# -------------------------------------------------------------------


def test_unauthenticated_user_cannot_create_leave(
    client: TestClient,
):
    start = future_weekday()

    response = client.post(
        "/api/leaves",
        json={
            "leave_type_id": 1,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert response.status_code == 401


def test_unauthenticated_user_cannot_get_leave(
    client: TestClient,
):
    response = client.get(
        "/api/leaves/999999",
    )

    assert response.status_code == 401


def test_admin_cannot_create_employee_leave(
    client: TestClient,
    db,
):
    admin = create_user(
        db,
        role=Role.ADMIN,
    )

    start = future_weekday()

    response = client.post(
        "/api/leaves",
        headers=auth_headers(admin),
        json={
            "leave_type_id": 1,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert response.status_code == 403



# -------------------------------------------------------------------
# Employee balances API
# -------------------------------------------------------------------


def test_employee_can_view_own_leave_balances(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
        balance=Decimal("20.00"),
    )

    # Set some used/reserved values to verify remaining_days.
    balance = db.scalar(
        select(LeaveBalance).where(
            LeaveBalance.user_id == employee.id,
            LeaveBalance.leave_type_id == leave_type.id,
            LeaveBalance.year == start.year,
        )
    )

    assert balance is not None

    balance.used_days = Decimal("5.00")
    balance.reserved_days = Decimal("2.00")
    db.commit()

    response = client.get(
        f"/api/employees/me/balances?year={start.year}",
        headers=auth_headers(employee),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["year"] == start.year
    assert data["total"] >= 1

    returned = next(
        item
        for item in data["items"]
        if item["leave_type_id"] == leave_type.id
    )

    assert returned["user_id"] == employee.id
    assert Decimal(returned["allocated_days"]) == Decimal("20.00")
    assert Decimal(returned["used_days"]) == Decimal("5.00")
    assert Decimal(returned["reserved_days"]) == Decimal("2.00")
    assert Decimal(returned["remaining_days"]) == Decimal("13.00")


def test_employee_only_sees_own_balances(
    client: TestClient,
    db,
):
    manager = create_manager(db)

    employee1 = create_employee(
        db,
        manager=manager,
    )

    employee2 = create_employee(
        db,
        manager=manager,
    )

    leave_type1 = create_leave_type(db)
    leave_type2 = create_leave_type(db)

    create_balance(
        db,
        employee=employee1,
        leave_type=leave_type1,
        year=2026,
    )

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type2,
        year=2026,
    )

    response = client.get(
        "/api/employees/me/balances?year=2026",
        headers=auth_headers(employee1),
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        item["user_id"] == employee1.id
        for item in data["items"]
    )

    assert not any(
        item["user_id"] == employee2.id
        for item in data["items"]
    )


def test_manager_can_view_own_leave_balances(
    client: TestClient,
    db,
):
    manager = create_manager(db)
    leave_type = create_leave_type(db)

    create_balance(
        db,
        employee=manager,
        leave_type=leave_type,
        year=2026,
        allocated=Decimal("15.00"),
    )

    response = client.get(
        "/api/employees/me/balances?year=2026",
        headers=auth_headers(manager),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["year"] == 2026

    returned = next(
        item
        for item in data["items"]
        if item["leave_type_id"] == leave_type.id
    )

    assert returned["user_id"] == manager.id
    assert Decimal(returned["allocated_days"]) == Decimal("15.00")


def test_admin_cannot_access_employee_balance_endpoint(
    client: TestClient,
    db,
):
    admin = create_user(
        db,
        role=Role.ADMIN,
    )

    response = client.get(
        "/api/employees/me/balances?year=2026",
        headers=auth_headers(admin),
    )

    assert response.status_code == 403


def test_missing_balance_returns_empty_balance_list(
    client: TestClient,
    db,
):
    manager = create_manager(db)

    employee = create_employee(
        db,
        manager=manager,
    )

    response = client.get(
        "/api/employees/me/balances?year=2026",
        headers=auth_headers(employee),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["year"] == 2026
    assert data["total"] == 0
    assert data["items"] == []


def test_invalid_balance_year_is_rejected(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    response = client.get(
        "/api/employees/me/balances?year=1999",
        headers=auth_headers(employee),
    )

    assert response.status_code == 422


def test_missing_balance_year_is_rejected(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    response = client.get(
        "/api/employees/me/balances",
        headers=auth_headers(employee),
    )

    assert response.status_code == 422


# -------------------------------------------------------------------
# Employee leave history API
# -------------------------------------------------------------------


def test_employee_can_view_own_leave_history(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
    )

    create_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
            "reason": "History test",
        },
    )

    assert create_response.status_code == 201

    request_id = create_response.json()["id"]

    response = client.get(
        "/api/employees/me/leaves",
        headers=auth_headers(employee),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    returned = next(
        item
        for item in data["items"]
        if item["id"] == request_id
    )

    assert returned["user_id"] == employee.id
    assert returned["reason"] == "History test"
    assert returned["status"] == LeaveStatus.PENDING.value


def test_employee_only_sees_own_leave_history(
    client: TestClient,
    db,
):
    manager = create_manager(db)

    employee1 = create_employee(
        db,
        manager=manager,
    )

    employee2 = create_employee(
        db,
        manager=manager,
    )

    leave_type1 = create_leave_type(db)
    leave_type2 = create_leave_type(db)

    start1 = future_weekday(7)
    start2 = future_weekday(14)

    create_balance(
        db,
        employee=employee1,
        leave_type=leave_type1,
        year=start1.year,
    )

    create_balance(
        db,
        employee=employee2,
        leave_type=leave_type2,
        year=start2.year,
    )

    response1 = client.post(
        "/api/leaves",
        headers=auth_headers(employee1),
        json={
            "leave_type_id": leave_type1.id,
            "start_date": start1.isoformat(),
            "end_date": start1.isoformat(),
        },
    )

    response2 = client.post(
        "/api/leaves",
        headers=auth_headers(employee2),
        json={
            "leave_type_id": leave_type2.id,
            "start_date": start2.isoformat(),
            "end_date": start2.isoformat(),
        },
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    employee1_request_id = response1.json()["id"]
    employee2_request_id = response2.json()["id"]

    history_response = client.get(
        "/api/employees/me/leaves",
        headers=auth_headers(employee1),
    )

    assert history_response.status_code == 200

    data = history_response.json()

    assert all(
        item["user_id"] == employee1.id
        for item in data["items"]
    )

    assert any(
        item["id"] == employee1_request_id
        for item in data["items"]
    )

    assert not any(
        item["id"] == employee2_request_id
        for item in data["items"]
    )


def test_manager_can_view_own_leave_history(
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

    response = client.get(
        "/api/employees/me/leaves",
        headers=auth_headers(manager),
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == request_id
        for item in data["items"]
    )


def test_leave_history_supports_pagination(
    client: TestClient,
    db,
):
    manager, employee, leave_type, start = create_employee_setup(
        db,
        balance=Decimal("10.00"),
    )

    first_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": start.isoformat(),
            "end_date": start.isoformat(),
        },
    )

    assert first_response.status_code == 201

    second_start = start + timedelta(days=3)

    while second_start.weekday() >= 5:
        second_start += timedelta(days=1)

    second_response = client.post(
        "/api/leaves",
        headers=auth_headers(employee),
        json={
            "leave_type_id": leave_type.id,
            "start_date": second_start.isoformat(),
            "end_date": second_start.isoformat(),
        },
    )

    assert second_response.status_code == 201

    response = client.get(
        "/api/employees/me/leaves?offset=0&limit=1",
        headers=auth_headers(employee),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 2
    assert len(data["items"]) == 1
    assert data["offset"] == 0
    assert data["limit"] == 1


def test_invalid_leave_history_limit_is_rejected(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    response = client.get(
        "/api/employees/me/leaves?limit=101",
        headers=auth_headers(employee),
    )

    assert response.status_code == 422


def test_negative_leave_history_offset_is_rejected(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    response = client.get(
        "/api/employees/me/leaves?offset=-1",
        headers=auth_headers(employee),
    )

    assert response.status_code == 422


def test_admin_cannot_access_employee_leave_history(
    client: TestClient,
    db,
):
    admin = create_user(
        db,
        role=Role.ADMIN,
    )

    response = client.get(
        "/api/employees/me/leaves",
        headers=auth_headers(admin),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_access_employee_leave_history(
    client: TestClient,
):
    response = client.get(
        "/api/employees/me/leaves",
    )

    assert response.status_code == 401