class AppError(Exception):
    """
    Base exception for application-specific errors.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# ---------------------------------------------------------
# Authentication / Authorization
# ---------------------------------------------------------


class AuthenticationError(AppError):
    """
    Raised when authentication fails.
    """
    pass


class AuthorizationError(AppError):
    """
    Raised when an authenticated user is not allowed
    to perform an action.
    """
    pass


# ---------------------------------------------------------
# Resource errors
# ---------------------------------------------------------


class ResourceNotFoundError(AppError):
    """
    Raised when a requested resource does not exist.
    """
    pass


class ResourceConflictError(AppError):
    """
    Raised when an operation conflicts with the current
    state of a resource.
    """
    pass


# ---------------------------------------------------------
# Leave-related business errors
# ---------------------------------------------------------


class InsufficientBalanceError(AppError):
    """
    Raised when the requested leave exceeds the
    available balance.
    """
    pass


class OverlappingLeaveError(AppError):
    """
    Raised when a leave request overlaps another
    pending or approved request.
    """
    pass


class InvalidLeaveDateError(AppError):
    """
    Raised when leave dates are invalid according to
    the business rules.
    """
    pass


class LeaveApprovalError(AppError):
    """
    Raised when a leave request cannot be approved.
    """
    pass


class LeaveCancellationError(AppError):
    """
    Raised when a leave request cannot be cancelled.
    """
    pass


class InvalidManagerError(AppError):
    """
    Raised when an invalid manager assignment is provided.
    """
    pass