
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import AuditAction, HalfDayType, LeaveStatus, Role
from app.core.exceptions import (
    AuthorizationError,
    InvalidLeaveDateError,
    LeaveApprovalError,
    LeaveCancellationError,
    InsufficientBalanceError,
    OverlappingLeaveError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.models.leave_request import LeaveRequest
from app.models.leave_request_allocation import LeaveRequestAllocation
from app.models.leave_type import LeaveType
from app.models.user import User
from app.services.audit_service import AuditService
from app.services.balance_service import BalanceService
from app.services.holiday_service import HolidayService
from app.services.working_days import calculate_working_days


class LeaveService:
    """
    Handles leave-request business logic.

    Responsibilities:
    - Create employee leave requests
    - Calculate working days
    - Exclude weekends and public holidays
    - Prevent overlapping leave
    - Validate yearly leave balances
    - Reserve/release/approve/restore balances
    - Handle manager approval/rejection
    - Handle employee cancellation
    - Create audit records

    Transaction management:
    The service does not commit the outer transaction.
    Mutating operations use a nested transaction/savepoint
    so that a multi-step operation is atomic.
    The caller is responsible for the final commit.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.balance_service = BalanceService(db)
        self.holiday_service = HolidayService(db)
        self.audit_service = AuditService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_pagination(offset: int, limit: int) -> None:
        if offset < 0:
            raise ValueError("Offset cannot be negative.")

        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100.")

    def _get_user(self, user_id: int) -> User:
        user = self.db.get(User, user_id)

        if user is None:
            raise ResourceNotFoundError("User not found.")

        return user

    def _get_active_employee(self, employee_id: int) -> User:
        employee = self._get_user(employee_id)

        if not employee.is_active:
            raise AuthorizationError(
                "User account is inactive."
            )

        if employee.role not in {
            Role.EMPLOYEE,
            Role.MANAGER,
        }:
            raise AuthorizationError(
                "Only employees and managers can request leave."
            )

        return employee

    def _get_active_manager(self, manager_id: int) -> User:
        manager = self._get_user(manager_id)

        if not manager.is_active:
            raise AuthorizationError("Manager account is inactive.")

        if manager.role != Role.MANAGER:
            raise AuthorizationError(
                "Only managers can perform this action."
            )

        return manager

    def _get_leave_request(self, request_id: int) -> LeaveRequest:
        request = self.db.get(LeaveRequest, request_id)

        if request is None:
            raise ResourceNotFoundError(
                "Leave request not found."
            )

        return request

    def _get_active_leave_type(self, leave_type_id: int) -> LeaveType:
        leave_type = self.db.scalar(
            select(LeaveType).where(
                LeaveType.id == leave_type_id,
                LeaveType.is_active.is_(True),
            )
        )

        if leave_type is None:
            raise ResourceNotFoundError(
                "Leave type not found or inactive."
            )

        return leave_type

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    def _validate_leave_dates(
        self,
        *,
        start_date: date,
        end_date: date,
    ) -> None:
        if end_date < start_date:
            raise InvalidLeaveDateError(
                "End date cannot be before start date."
            )

        today = datetime.now(timezone.utc).date()

        if start_date < today:
            raise InvalidLeaveDateError(
                "Leave cannot start in the past."
            )

    # ------------------------------------------------------------------
    # Overlap detection
    # ------------------------------------------------------------------

    def _check_overlap(
        self,
        *,
        employee_id: int,
        start_date: date,
        end_date: date,
        exclude_request_id: int | None = None,
    ) -> None:
        """
        Prevent overlap with PENDING or APPROVED leave.

        Date ranges are treated inclusively.

        Example:

            Existing: 10 Oct - 12 Oct
            New:      12 Oct - 15 Oct

        These overlap because 12 Oct is included in both ranges.
        """

        statement = select(LeaveRequest.id).where(
            LeaveRequest.user_id == employee_id,
            LeaveRequest.status.in_(
                [
                    LeaveStatus.PENDING,
                    LeaveStatus.APPROVED,
                ]
            ),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )

        if exclude_request_id is not None:
            statement = statement.where(
                LeaveRequest.id != exclude_request_id
            )

        existing_id = self.db.scalar(statement.limit(1))

        if existing_id is not None:
            raise OverlappingLeaveError(
                "Leave request overlaps an existing pending or "
                "approved leave request."
            )

    # ------------------------------------------------------------------
    # Yearly allocation
    # ------------------------------------------------------------------

    def _calculate_yearly_allocations(
        self,
        *,
        start_date: date,
        end_date: date,
        start_half_day: HalfDayType,
        end_half_day: HalfDayType,
    ) -> list[tuple[int, Decimal]]:
        """
        Calculate leave days separately for each calendar year.

        This supports requests such as:

            30 Dec 2026 -> 5 Jan 2027

        Example:

            2026 -> 2.00 days
            2027 -> 3.00 days
        """

        holidays = self.holiday_service.get_holiday_dates(
            start_date,
            end_date,
        )

        allocations: list[tuple[int, Decimal]] = []

        current_year = start_date.year

        while current_year <= end_date.year:
            if current_year == start_date.year:
                segment_start = start_date
            else:
                segment_start = date(current_year, 1, 1)

            if current_year == end_date.year:
                segment_end = end_date
            else:
                segment_end = date(current_year, 12, 31)

            segment_start_half_day = (
                start_half_day
                if current_year == start_date.year
                else HalfDayType.NONE
            )

            segment_end_half_day = (
                end_half_day
                if current_year == end_date.year
                else HalfDayType.NONE
            )

            days = calculate_working_days(
                start_date=segment_start,
                end_date=segment_end,
                holidays=holidays,
                start_half_day=segment_start_half_day,
                end_half_day=segment_end_half_day,
            )

            if days > Decimal("0.00"):
                allocations.append(
                    (
                        current_year,
                        days,
                    )
                )

            current_year += 1

        if not allocations:
            raise InvalidLeaveDateError(
                "Leave request must contain at least one working day."
            )

        return allocations

    # ------------------------------------------------------------------
    # Balance validation
    # ------------------------------------------------------------------

    def _validate_balances(
        self,
        *,
        employee_id: int,
        leave_type_id: int,
        allocations: list[tuple[int, Decimal]],
    ) -> None:
        """
        Validate all yearly balances before modifying any balance.

        This prevents a year-spanning request from partially passing
        validation.
        """

        for year, days in allocations:
            balance = self.balance_service.get_balance(
                user_id=employee_id,
                leave_type_id=leave_type_id,
                year=year,
            )

            if balance.remaining_days < days:
                raise InsufficientBalanceError(
                    f"Insufficient leave balance for {year}."
                )

    def _reserve_allocations(
        self,
        *,
        employee_id: int,
        leave_type_id: int,
        allocations: list[tuple[int, Decimal]],
    ) -> None:
        for year, days in allocations:
            self.balance_service.reserve_days(
                user_id=employee_id,
                leave_type_id=leave_type_id,
                year=year,
                days=days,
            )

    def _release_allocations(
        self,
        *,
        employee_id: int,
        leave_type_id: int,
        allocations: list[LeaveRequestAllocation],
    ) -> None:
        for allocation in allocations:
            self.balance_service.release_reserved_days(
                user_id=employee_id,
                leave_type_id=leave_type_id,
                year=allocation.year,
                days=allocation.allocated_days,
            )

    def _approve_allocations(
        self,
        *,
        employee_id: int,
        leave_type_id: int,
        allocations: list[LeaveRequestAllocation],
    ) -> None:
        for allocation in allocations:
            self.balance_service.approve_reserved_days(
                user_id=employee_id,
                leave_type_id=leave_type_id,
                year=allocation.year,
                days=allocation.allocated_days,
            )

    def _restore_allocations(
        self,
        *,
        employee_id: int,
        leave_type_id: int,
        allocations: list[LeaveRequestAllocation],
    ) -> None:
        for allocation in allocations:
            self.balance_service.restore_used_days(
                user_id=employee_id,
                leave_type_id=leave_type_id,
                year=allocation.year,
                days=allocation.allocated_days,
            )

    # ------------------------------------------------------------------
    # Create leave request
    # ------------------------------------------------------------------

    def create_leave_request(
        self,
        *,
        employee_id: int,
        leave_type_id: int,
        start_date: date,
        end_date: date,
        start_half_day: HalfDayType = HalfDayType.NONE,
        end_half_day: HalfDayType = HalfDayType.NONE,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LeaveRequest:
        employee = self._get_active_employee(employee_id)

        self._validate_leave_dates(
            start_date=start_date,
            end_date=end_date,
        )

        leave_type = self._get_active_leave_type(leave_type_id)

        self._check_overlap(
            employee_id=employee.id,
            start_date=start_date,
            end_date=end_date,
        )

        allocations = self._calculate_yearly_allocations(
            start_date=start_date,
            end_date=end_date,
            start_half_day=start_half_day,
            end_half_day=end_half_day,
        )

        self._validate_balances(
            employee_id=employee.id,
            leave_type_id=leave_type.id,
            allocations=allocations,
        )

        total_days = sum(
            (days for _, days in allocations),
            Decimal("0.00"),
        )

        normalized_reason = self._normalize_text(reason)

        with self.db.begin_nested():
            self._reserve_allocations(
                employee_id=employee.id,
                leave_type_id=leave_type.id,
                allocations=allocations,
            )

            request = LeaveRequest(
                user_id=employee.id,
                leave_type_id=leave_type.id,
                start_date=start_date,
                end_date=end_date,
                start_half_day=start_half_day,
                end_half_day=end_half_day,
                total_days=total_days,
                reason=normalized_reason,
                status=LeaveStatus.PENDING,
            )

            self.db.add(request)
            self.db.flush()

            for year, days in allocations:
                self.db.add(
                    LeaveRequestAllocation(
                        leave_request_id=request.id,
                        year=year,
                        allocated_days=days,
                    )
                )

            self.audit_service.log(
                user_id=employee.id,
                action=AuditAction.CREATE_LEAVE
                if hasattr(AuditAction, "CREATE_LEAVE")
                else AuditAction.CANCEL_LEAVE,
                entity_type="leave_request",
                entity_id=request.id,
                details={
                    "status": LeaveStatus.PENDING.value,
                    "total_days": str(total_days),
                    "leave_type_id": leave_type.id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            self.db.flush()

        return request

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_request(
        self,
        *,
        request_id: int,
    ) -> LeaveRequest:
        return self._get_leave_request(request_id)

    def list_employee_requests(
        self,
        *,
        employee_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[LeaveRequest], int]:
        self._validate_pagination(offset, limit)

        self._get_active_employee(employee_id)

        base_filter = (
            LeaveRequest.user_id == employee_id
        )

        total = self.db.scalar(
            select(func.count(LeaveRequest.id)).where(
                base_filter
            )
        ) or 0

        items = list(
            self.db.scalars(
                select(LeaveRequest)
                .where(base_filter)
                .order_by(
                    LeaveRequest.start_date.desc(),
                    LeaveRequest.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            ).all()
        )

        return items, total

    def list_team_requests(
        self,
        *,
        manager_id: int,
        offset: int = 0,
        limit: int = 50,
        status: LeaveStatus | None = None,
    ) -> tuple[list[LeaveRequest], int]:
        self._validate_pagination(offset, limit)

        manager = self._get_active_manager(manager_id)

        filters = [
            User.manager_id == manager.id,
        ]

        if status is not None:
            filters.append(
                LeaveRequest.status == status
            )

        statement = (
            select(LeaveRequest)
            .join(
                User,
                User.id == LeaveRequest.user_id,
            )
            .where(*filters)
        )

        count_statement = (
            select(func.count(LeaveRequest.id))
            .join(
                User,
                User.id == LeaveRequest.user_id,
            )
            .where(*filters)
        )

        total = self.db.scalar(count_statement) or 0

        items = list(
            self.db.scalars(
                statement
                .order_by(
                    LeaveRequest.start_date.desc(),
                    LeaveRequest.id.desc(),
                )
                .offset(offset)
                .limit(limit)
            ).all()
        )

        return items, total

    # ------------------------------------------------------------------
    # Manager authorization
    # ------------------------------------------------------------------

    def _validate_manager_ownership(
        self,
        *,
        manager: User,
        request: LeaveRequest,
    ) -> User:
        if request.user_id == manager.id:
            raise AuthorizationError(
                "A manager cannot approve or reject their own leave."
            )

        employee = self._get_user(request.user_id)

        if employee.manager_id != manager.id:
            raise AuthorizationError(
                "You can only manage leave requests from your own team."
            )

        return employee

    # ------------------------------------------------------------------
    # Approve
    # ------------------------------------------------------------------

    def approve_leave_request(
        self,
        *,
        manager_id: int,
        request_id: int,
        comment: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LeaveRequest:
        manager = self._get_active_manager(manager_id)
        request = self._get_leave_request(request_id)

        if request.status != LeaveStatus.PENDING:
            raise LeaveApprovalError(
                "Only pending leave requests can be approved."
            )

        employee = self._validate_manager_ownership(
            manager=manager,
            request=request,
        )

        normalized_comment = self._normalize_text(comment)

        allocations = list(request.allocations)

        if not allocations:
            raise ResourceConflictError(
                "Leave request has no yearly allocations."
            )

        with self.db.begin_nested():
            self._approve_allocations(
                employee_id=employee.id,
                leave_type_id=request.leave_type_id,
                allocations=allocations,
            )

            request.status = LeaveStatus.APPROVED
            request.approved_by_id = manager.id
            request.approval_comment = normalized_comment
            request.approved_at = datetime.now(timezone.utc)

            self.audit_service.log(
                user_id=manager.id,
                action=AuditAction.APPROVE_LEAVE,
                entity_type="leave_request",
                entity_id=request.id,
                details={
                    "employee_id": employee.id,
                    "total_days": str(request.total_days),
                    "comment": normalized_comment,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            self.db.flush()

        return request

    # ------------------------------------------------------------------
    # Reject
    # ------------------------------------------------------------------

    def reject_leave_request(
        self,
        *,
        manager_id: int,
        request_id: int,
        comment: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LeaveRequest:
        manager = self._get_active_manager(manager_id)
        request = self._get_leave_request(request_id)

        if request.status != LeaveStatus.PENDING:
            raise LeaveApprovalError(
                "Only pending leave requests can be rejected."
            )

        employee = self._validate_manager_ownership(
            manager=manager,
            request=request,
        )

        normalized_comment = self._normalize_text(comment)

        allocations = list(request.allocations)

        if not allocations:
            raise ResourceConflictError(
                "Leave request has no yearly allocations."
            )

        with self.db.begin_nested():
            self._release_allocations(
                employee_id=employee.id,
                leave_type_id=request.leave_type_id,
                allocations=allocations,
            )

            request.status = LeaveStatus.REJECTED
            request.approval_comment = normalized_comment

            self.audit_service.log(
                user_id=manager.id,
                action=AuditAction.REJECT_LEAVE,
                entity_type="leave_request",
                entity_id=request.id,
                details={
                    "employee_id": employee.id,
                    "total_days": str(request.total_days),
                    "comment": normalized_comment,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            self.db.flush()

        return request

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    def cancel_leave_request(
        self,
        *,
        employee_id: int,
        request_id: int,
        reason: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> LeaveRequest:
        employee = self._get_active_employee(employee_id)
        request = self._get_leave_request(request_id)

        if request.user_id != employee.id:
            raise AuthorizationError(
                "You can only cancel your own leave requests."
            )

        if request.status not in {
            LeaveStatus.PENDING,
            LeaveStatus.APPROVED,
        }:
            raise LeaveCancellationError(
                "Only pending or approved leave can be cancelled."
            )

        normalized_reason = self._normalize_text(reason)

        allocations = list(request.allocations)

        if not allocations:
            raise ResourceConflictError(
                "Leave request has no yearly allocations."
            )
        previous_status = request.status

        with self.db.begin_nested():
            if previous_status == LeaveStatus.PENDING:
                self._release_allocations(
                    employee_id=employee.id,
                    leave_type_id=request.leave_type_id,
                    allocations=allocations,
                )

            elif previous_status == LeaveStatus.APPROVED:
                self._restore_allocations(
                    employee_id=employee.id,
                    leave_type_id=request.leave_type_id,
                    allocations=allocations,
                )

            request.status = LeaveStatus.CANCELLED
            request.cancelled_by_id = employee.id
            request.cancellation_reason = normalized_reason
            request.cancelled_at = datetime.now(timezone.utc)

            self.audit_service.log(
                user_id=employee.id,
                action=AuditAction.CANCEL_LEAVE,
                entity_type="leave_request",
                entity_id=request.id,
                details={
                    "previous_status": previous_status.value,
                    "total_days": str(request.total_days),
                    "reason": normalized_reason,
                },
                ip_address=ip_address,
                user_agent=user_agent,
            )

            self.db.flush()

        return request