from datetime import timedelta
from uuid import uuid4

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.core.enums import Role


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------


def unique_email(prefix: str = "auth-test") -> str:
    return f"{prefix}-{uuid4().hex[:10]}@example.com"


def create_user(
    db,
    *,
    password: str = "StrongPassword123!",
    role: Role = Role.EMPLOYEE,
    is_active: bool = True,
) -> User:
    user = User(
        first_name="Auth",
        last_name="Tester",
        email=unique_email(),
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# -------------------------------------------------------------------
# Login
# -------------------------------------------------------------------


def test_valid_login_returns_access_token(client, db):
    password = "StrongPassword123!"
    user = create_user(
        db,
        password=password,
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_wrong_password_returns_401(client, db):
    user = create_user(db)

    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]


def test_unknown_email_returns_401(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": unique_email("unknown"),
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]


def test_inactive_user_cannot_login(client, db):
    password = "StrongPassword123!"

    user = create_user(
        db,
        password=password,
        is_active=False,
    )

    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert response.status_code == 401


def test_successful_login_resets_failed_attempts(client, db):
    password = "StrongPassword123!"

    user = create_user(
        db,
        password=password,
    )

    user.failed_login_attempts = 2
    db.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert response.status_code == 200

    db.refresh(user)

    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    assert user.last_login_at is not None


def test_failed_login_increments_failed_attempts(client, db):
    user = create_user(db)

    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    db.refresh(user)

    assert user.failed_login_attempts == 1


def test_account_is_locked_after_max_failed_attempts(client, db):
    password = "StrongPassword123!"

    user = create_user(
        db,
        password=password,
    )

    for _ in range(settings.MAX_LOGIN_ATTEMPTS):
        response = client.post(
            "/api/auth/login",
            json={
                "email": user.email,
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    db.refresh(user)

    assert user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS
    assert user.locked_until is not None

    # Correct password should still fail while the account is locked.
    response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert response.status_code == 401


# -------------------------------------------------------------------
# /me
# -------------------------------------------------------------------


def test_authenticated_user_can_access_me(client, db):
    password = "StrongPassword123!"

    user = create_user(
        db,
        password=password,
        role=Role.EMPLOYEE,
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()
    print(data)

    assert data["id"] == user.id
    assert data["first_name"] == "Auth"
    assert data["last_name"] == "Tester"
    assert data["email"] == user.email
    assert data["role"] == Role.EMPLOYEE.value
    assert data["is_active"] is True


def test_missing_token_returns_401(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_invalid_token_returns_401(client):
    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer this-is-not-a-valid-token",
        },
    )

    assert response.status_code == 401


def test_expired_token_returns_401(client, db):
    user = create_user(db)

    token = create_access_token(
        subject=str(user.id),
        token_version=user.token_version,
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401


def test_inactive_user_token_is_rejected(client, db):
    password = "StrongPassword123!"

    user = create_user(
        db,
        password=password,
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    user.is_active = False
    db.commit()

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401


def test_old_token_is_rejected_after_token_version_changes(
    client,
    db,
):
    password = "StrongPassword123!"

    user = create_user(
        db,
        password=password,
    )

    login_response = client.post(
        "/api/auth/login",
        json={
            "email": user.email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Verify the token works before invalidation.
    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    # Increment token_version to invalidate all previously
    # issued tokens for this user.
    user.token_version += 1
    db.commit()

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401


def test_wrong_jwt_token_type_is_rejected(client, db):
    user = create_user(db)

    payload = {
        "sub": str(user.id),
        "type": "refresh",
        "ver": user.token_version,
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401