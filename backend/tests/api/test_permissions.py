from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.enums import Role
from app.core.security import create_access_token, hash_password
from app.models.user import User


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def unique_email(role: Role) -> str:
    return f"{role.value.lower()}-{uuid4().hex[:10]}@example.com"


def create_user(
    db,
    *,
    role: Role,
) -> User:
    user = User(
        first_name="Permission",
        last_name="Tester",
        email=unique_email(role),
        password_hash=hash_password("StrongPassword123!"),
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def auth_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        subject=str(user.id),
        token_version=user.token_version,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


# -------------------------------------------------------------------
# Admin endpoint
# -------------------------------------------------------------------
def test_admin_can_access_admin_users_endpoint(
    client: TestClient,
    db,
):
    admin = create_user(
        db,
        role=Role.ADMIN,
    )

    response = client.get(
        "/api/admin/users?limit=100",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    assert any(
        user["role"] == Role.ADMIN.value
        for user in data
    )

def test_employee_cannot_access_admin_users_endpoint(
    client: TestClient,
    db,
):
    employee = create_user(
        db,
        role=Role.EMPLOYEE,
    )

    response = client.get(
        "/api/admin/users",
        headers=auth_headers(employee),
    )

    assert response.status_code == 403


def test_manager_cannot_access_admin_users_endpoint(
    client: TestClient,
    db,
):
    manager = create_user(
        db,
        role=Role.MANAGER,
    )

    response = client.get(
        "/api/admin/users",
        headers=auth_headers(manager),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_access_admin_users_endpoint(
    client: TestClient,
):
    response = client.get(
        "/api/admin/users",
    )

    assert response.status_code == 401


def test_invalid_token_returns_401(client: TestClient):
    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401


def test_malformed_authorization_header_returns_401(
    client: TestClient,
):
    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": "NotBearer token",
        },
    )

    assert response.status_code == 401


def test_inactive_admin_cannot_access_admin_endpoint(
    client: TestClient,
    db,
):
    admin = create_user(
        db,
        role=Role.ADMIN,
    )

    admin.is_active = False
    db.commit()

    response = client.get(
        "/api/admin/users",
        headers=auth_headers(admin),
    )

    assert response.status_code == 401


def test_token_version_change_invalidates_existing_admin_token(
    client: TestClient,
    db,
):
    admin = create_user(
        db,
        role=Role.ADMIN,
    )

    token = create_access_token(
        subject=str(admin.id),
        token_version=admin.token_version,
    )

    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    admin.token_version += 1
    db.commit()

    response = client.get(
        "/api/admin/users",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401