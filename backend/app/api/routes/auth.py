from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    LoginRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate a user and return a JWT access token in an HTTP-only cookie.
    """

    try:
        auth_service = AuthService(db)
        token_response = auth_service.login(login_data)

        # Set HTTP-only cookie for secure session authentication
        is_production = settings.ENVIRONMENT.lower() == "production"
        max_age_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60

        response.set_cookie(
            key="access_token",
            value=token_response.access_token,
            httponly=True,
            max_age=max_age_seconds,
            expires=max_age_seconds,
            samesite="none",
            secure=is_production,
            path="/",
        )

        return token_response

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    """
    Return the currently authenticated user's profile.
    """

    return CurrentUserResponse.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
def logout(response: Response):
    """
    Logout user endpoint and clear HTTP-only access_token cookie.
    """
    is_production = settings.ENVIRONMENT.lower() == "production"
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=is_production,
        path="/",
    )
    return {"message": "Logged out successfully"}

