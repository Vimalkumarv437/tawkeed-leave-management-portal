from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.enums import Role
from app.dependencies.auth import get_current_user
from app.models.user import User


def require_role(*allowed_roles: Role) -> Callable:
    """
    Create a FastAPI dependency that allows only users
    with one of the specified roles.

    Example:
        Depends(require_role(Role.ADMIN))

    or:
        Depends(require_role(Role.ADMIN, Role.MANAGER))
    """

    if not allowed_roles:
        raise ValueError(
            "At least one allowed role must be provided."
        )

    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """
        Verify that the authenticated user has an allowed role.
        """

        if current_user.role not in allowed_roles:
            allowed_role_names = ", ".join(
                role.value for role in allowed_roles
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role: "
                    f"{allowed_role_names}."
                ),
            )

        return current_user

    return role_checker