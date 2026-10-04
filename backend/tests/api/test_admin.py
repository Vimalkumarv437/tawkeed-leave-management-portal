from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.enums import Role
from app.core.security import create_access_token, hash_password
from app.models.leave_balance import LeaveBalance
from app.models.leave_type import LeaveType
from app.models.public_holiday import PublicHoliday
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
    is_active: bool = True,
) -> User:
    user = User(
        first_name="Admin",
        last_name="Tester",
        email=f"{unique_value('user')}@example.com",
        password_hash=hash_password("StrongPassword123!"),
        role=role,
        manager_id=manager_id,
        is_active=is_active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def create_admin(db) -> User:
    return create_user(
        db,
        role=Role.ADMIN,
    )


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


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        token_version=user.token_version,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def create_leave_type(
    db,
    *,
    allowance: Decimal = Decimal("20.00"),
) -> LeaveType:
    leave_type = LeaveType(
        name=unique_value("Leave"),
        code=unique_value("CODE").upper(),
        description="Admin API test leave type",
        default_annual_allowance=allowance,
        is_active=True,
    )

    db.add(leave_type)
    db.commit()
    db.refresh(leave_type)

    return leave_type


# -------------------------------------------------------------------
# User management
# -------------------------------------------------------------------


def test_admin_can_list_users(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
        manager_id=None,
    )

    response = client.get(
        "/api/admin/users?limit=100",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    returned = next(
        user
        for user in data
        if user["id"] == employee.id
    )

    assert returned["email"] == employee.email
    assert returned["role"] == Role.EMPLOYEE.value


def test_admin_can_filter_users_by_role(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    manager = create_manager(db)

    response = client.get(
        "/api/admin/users?role=MANAGER&limit=100",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert all(
        user["role"] == Role.MANAGER.value
        for user in data
    )

    assert any(
        user["id"] == manager.id
        for user in data
    )


def test_admin_can_filter_users_by_active_status(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    active_user = create_manager(db)
    inactive_user = create_manager(db)

    inactive_user.is_active = False
    db.commit()

    response = client.get(
        "/api/admin/users?is_active=true&limit=100",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    ids = {user["id"] for user in data}

    assert active_user.id in ids
    assert inactive_user.id not in ids


def test_admin_can_create_employee(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    manager = create_manager(db)

    email = f"{unique_value('employee')}@example.com"

    response = client.post(
        "/api/admin/users",
        headers=auth_headers(admin),
        json={
            "first_name": "John",
            "last_name": "Employee",
            "email": email,
            "password": "StrongPassword123!",
            "role": "EMPLOYEE",
            "manager_id": manager.id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["first_name"] == "John"
    assert data["last_name"] == "Employee"
    assert data["email"] == email.lower()
    assert data["role"] == "EMPLOYEE"
    assert data["manager_id"] == manager.id
    assert data["is_active"] is True


def test_admin_can_create_manager(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    email = f"{unique_value('manager')}@example.com"

    response = client.post(
        "/api/admin/users",
        headers=auth_headers(admin),
        json={
            "first_name": "New",
            "last_name": "Manager",
            "email": email,
            "password": "StrongPassword123!",
            "role": "MANAGER",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == email.lower()
    assert data["role"] == "MANAGER"
    assert data["manager_id"] is None


def test_admin_create_employee_without_manager_is_rejected(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    response = client.post(
        "/api/admin/users",
        headers=auth_headers(admin),
        json={
            "first_name": "No",
            "last_name": "Manager",
            "email": f"{unique_value('nomgr')}@example.com",
            "password": "StrongPassword123!",
            "role": "EMPLOYEE",
        },
    )

    assert response.status_code == 422


def test_admin_create_employee_with_invalid_manager_is_rejected(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    response = client.post(
        "/api/admin/users",
        headers=auth_headers(admin),
        json={
            "first_name": "Invalid",
            "last_name": "Manager",
            "email": f"{unique_value('badmgr')}@example.com",
            "password": "StrongPassword123!",
            "role": "EMPLOYEE",
            "manager_id": 999999,
        },
    )

    assert response.status_code in {404, 400}


def test_admin_rejects_duplicate_email(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    manager = create_manager(db)
    employee = create_employee(
        db,
        manager=manager,
    )

    response = client.post(
        "/api/admin/users",
        headers=auth_headers(admin),
        json={
            "first_name": "Duplicate",
            "last_name": "Email",
            "email": employee.email,
            "password": "StrongPassword123!",
            "role": "EMPLOYEE",
            "manager_id": manager.id,
        },
    )

    assert response.status_code == 409


def test_admin_can_update_employee(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    manager1 = create_manager(db)
    manager2 = create_manager(db)

    employee = create_employee(
        db,
        manager=manager1,
    )

    response = client.patch(
        f"/api/admin/users/{employee.id}",
        headers=auth_headers(admin),
        json={
            "first_name": "Updated",
            "last_name": "Employee",
            "manager_id": manager2.id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Employee"
    assert data["manager_id"] == manager2.id


def test_admin_can_deactivate_user(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    manager = create_manager(db)

    response = client.delete(
        f"/api/admin/users/{manager.id}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_active"] is False


def test_admin_can_reactivate_user(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    manager = create_manager(db)

    manager.is_active = False
    db.commit()

    response = client.post(
        f"/api/admin/users/{manager.id}/reactivate",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_active"] is True


# -------------------------------------------------------------------
# Leave types
# -------------------------------------------------------------------


def test_admin_can_list_leave_types(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    leave_type = create_leave_type(db)

    response = client.get(
        "/api/admin/leave-types?limit=100",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    returned = next(
        item
        for item in data["items"]
        if item["id"] == leave_type.id
    )

    assert returned["code"] == leave_type.code


def test_admin_can_create_leave_type(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    response = client.post(
        "/api/admin/leave-types",
        headers=auth_headers(admin),
        json={
            "name": "Annual Leave",
            "code": "ANNUAL",
            "description": "Annual vacation",
            "default_annual_allowance": "20.00",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Annual Leave"
    assert data["code"] == "ANNUAL"
    assert Decimal(data["default_annual_allowance"]) == Decimal("20.00")
    assert data["is_active"] is True


def test_admin_can_update_leave_type(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    leave_type = create_leave_type(db)

    response = client.patch(
        f"/api/admin/leave-types/{leave_type.id}",
        headers=auth_headers(admin),
        json={
            "name": "Updated Leave Type",
            "default_annual_allowance": "25.00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Leave Type"
    assert Decimal(data["default_annual_allowance"]) == Decimal("25.00")
    assert data["code"] == leave_type.code


def test_admin_duplicate_leave_type_code_is_rejected(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    existing = create_leave_type(
        db,
        allowance=Decimal("10.00"),
    )

    response = client.post(
        "/api/admin/leave-types",
        headers=auth_headers(admin),
        json={
            "name": unique_value("Different"),
            "code": existing.code,
            "description": "Duplicate code",
            "default_annual_allowance": "10.00",
            "is_active": True,
        },
    )

    assert response.status_code == 409


# -------------------------------------------------------------------
# Yearly balances
# -------------------------------------------------------------------


def test_admin_can_list_balances(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance = LeaveBalance(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("20.00"),
        used_days=Decimal("0.00"),
        reserved_days=Decimal("0.00"),
    )

    db.add(balance)
    db.commit()
    db.refresh(balance)

    response = client.get(
        "/api/admin/balances?limit=100",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    returned = next(
        item
        for item in data["items"]
        if item["id"] == balance.id
    )

    assert returned["user_id"] == employee.id
    assert returned["leave_type_id"] == leave_type.id
    assert returned["year"] == 2026


def test_admin_can_filter_balances_by_year(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    for year in (2026, 2027):
        db.add(
            LeaveBalance(
                user_id=employee.id,
                leave_type_id=leave_type.id,
                year=year,
                allocated_days=Decimal("20.00"),
                used_days=Decimal("0.00"),
                reserved_days=Decimal("0.00"),
            )
        )

    db.commit()

    response = client.get(
        "/api/admin/balances?year=2026&limit=100",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert all(
        item["year"] == 2026
        for item in data["items"]
    )


def test_admin_can_create_balance(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    response = client.post(
        "/api/admin/balances",
        headers=auth_headers(admin),
        json={
            "user_id": employee.id,
            "leave_type_id": leave_type.id,
            "year": 2026,
            "allocated_days": "20.00",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == employee.id
    assert data["leave_type_id"] == leave_type.id
    assert data["year"] == 2026
    assert Decimal(data["allocated_days"]) == Decimal("20.00")
    assert Decimal(data["used_days"]) == Decimal("0.00")
    assert Decimal(data["reserved_days"]) == Decimal("0.00")


def test_admin_cannot_create_duplicate_balance(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    db.add(
        LeaveBalance(
            user_id=employee.id,
            leave_type_id=leave_type.id,
            year=2026,
            allocated_days=Decimal("20.00"),
            used_days=Decimal("0.00"),
            reserved_days=Decimal("0.00"),
        )
    )
    db.commit()

    response = client.post(
        "/api/admin/balances",
        headers=auth_headers(admin),
        json={
            "user_id": employee.id,
            "leave_type_id": leave_type.id,
            "year": 2026,
            "allocated_days": "20.00",
        },
    )

    assert response.status_code == 409


def test_admin_can_update_balance(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance = LeaveBalance(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("20.00"),
        used_days=Decimal("5.00"),
        reserved_days=Decimal("2.00"),
    )

    db.add(balance)
    db.commit()
    db.refresh(balance)

    response = client.patch(
        f"/api/admin/balances/{balance.id}",
        headers=auth_headers(admin),
        json={
            "allocated_days": "15.00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(data["allocated_days"]) == Decimal("15.00")
    assert Decimal(data["used_days"]) == Decimal("5.00")
    assert Decimal(data["reserved_days"]) == Decimal("2.00")


def test_admin_cannot_reduce_balance_below_used_plus_reserved(
    client: TestClient,
    db,
):
    admin = create_admin(db)
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    balance = LeaveBalance(
        user_id=employee.id,
        leave_type_id=leave_type.id,
        year=2026,
        allocated_days=Decimal("20.00"),
        used_days=Decimal("5.00"),
        reserved_days=Decimal("3.00"),
    )

    db.add(balance)
    db.commit()
    db.refresh(balance)

    response = client.patch(
        f"/api/admin/balances/{balance.id}",
        headers=auth_headers(admin),
        json={
            "allocated_days": "7.00",
        },
    )

    assert response.status_code == 409


# -------------------------------------------------------------------
# Public holidays
# -------------------------------------------------------------------
def unique_holiday_date() -> date:
    return date(2050, 1, 1) + timedelta(
        days=uuid4().int % 10000
    )

def test_admin_can_list_holidays(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    holiday_date = unique_holiday_date()

    holiday = PublicHoliday(
        holiday_date=holiday_date,
        name="New Year",
        description="New Year holiday",
    )

    db.add(holiday)
    db.commit()
    db.refresh(holiday)

    response = client.get(
        "/api/admin/holidays",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    returned = next(
        item
        for item in data["items"]
        if item["id"] == holiday.id
    )

    assert returned["name"] == "New Year"


def test_admin_can_filter_holidays_by_date_range(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    first_date = unique_holiday_date()
    second_date = first_date + timedelta(days=30)

    db.add_all(
        [
            PublicHoliday(
                holiday_date=first_date,
                name="Holiday One",
            ),
            PublicHoliday(
                holiday_date=second_date,
                name="Holiday Two",
            ),
        ]
    )
    db.commit()

    response = client.get(
        "/api/admin/holidays"
        f"?start_date={first_date.isoformat()}"
        f"&end_date={(first_date + timedelta(days=10)).isoformat()}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["holiday_date"] == first_date.isoformat()
    assert data["items"][0]["name"] == "Holiday One"


def test_admin_can_create_holiday(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    response = client.post(
        "/api/admin/holidays",
        headers=auth_headers(admin),
        json={
            "holiday_date": "2027-08-15",
            "name": "Independence Day",
            "description": "Public holiday",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["holiday_date"] == "2027-08-15"
    assert data["name"] == "Independence Day"
    assert data["description"] == "Public holiday"


def test_admin_duplicate_holiday_date_is_rejected(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    holiday_date = unique_holiday_date()

    db.add(
        PublicHoliday(
            holiday_date=holiday_date,
            name="Existing Holiday",
        )
    )
    db.commit()

    response = client.post(
        "/api/admin/holidays",
        headers=auth_headers(admin),
        json={
            "holiday_date": holiday_date.isoformat(),
            "name": "Duplicate Holiday",
        },
    )

    assert response.status_code == 409

def test_admin_can_update_holiday(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    holiday = PublicHoliday(
        holiday_date="2027-05-01",
        name="Old Holiday",
        description="Old",
    )

    db.add(holiday)
    db.commit()
    db.refresh(holiday)

    response = client.patch(
        f"/api/admin/holidays/{holiday.id}",
        headers=auth_headers(admin),
        json={
            "name": "Labour Day",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Labour Day"
    assert data["description"] == "Updated description"


def test_admin_can_delete_holiday(
    client: TestClient,
    db,
):
    admin = create_admin(db)

    holiday = PublicHoliday(
        holiday_date="2027-10-02",
        name="Gandhi Jayanti",
    )

    db.add(holiday)
    db.commit()
    db.refresh(holiday)

    response = client.delete(
        f"/api/admin/holidays/{holiday.id}",
        headers=auth_headers(admin),
    )

    assert response.status_code == 204

    deleted = db.get(
        PublicHoliday,
        holiday.id,
    )

    assert deleted is None


# -------------------------------------------------------------------
# Admin-only access
# -------------------------------------------------------------------


def test_employee_cannot_create_user(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    response = client.post(
        "/api/admin/users",
        headers=auth_headers(employee),
        json={
            "first_name": "Blocked",
            "last_name": "User",
            "email": f"{unique_value('blocked')}@example.com",
            "password": "StrongPassword123!",
            "role": "MANAGER",
        },
    )

    assert response.status_code == 403


def test_manager_cannot_create_leave_type(
    client: TestClient,
    db,
):
    manager = create_manager(db)

    response = client.post(
        "/api/admin/leave-types",
        headers=auth_headers(manager),
        json={
            "name": "Blocked Leave",
            "code": unique_value("BLOCKED"),
            "default_annual_allowance": "10.00",
            "is_active": True,
        },
    )

    assert response.status_code == 403


def test_employee_cannot_create_balance(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )
    leave_type = create_leave_type(db)

    response = client.post(
        "/api/admin/balances",
        headers=auth_headers(employee),
        json={
            "user_id": employee.id,
            "leave_type_id": leave_type.id,
            "year": 2026,
            "allocated_days": "20.00",
        },
    )

    assert response.status_code == 403


def test_manager_cannot_create_holiday(
    client: TestClient,
    db,
):
    manager = create_manager(db)

    response = client.post(
        "/api/admin/holidays",
        headers=auth_headers(manager),
        json={
            "holiday_date": "2027-11-14",
            "name": "Blocked Holiday",
        },
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_access_admin_users(
    client: TestClient,
):
    response = client.get(
        "/api/admin/users",
    )

    assert response.status_code == 401
    