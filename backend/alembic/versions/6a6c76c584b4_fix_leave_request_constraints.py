"""fix leave request constraints

Revision ID: 6a6c76c584b4
Revises: c48b031db54c
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "6a6c76c584b4"
down_revision: Union[str, Sequence[str], None] = "c48b031db54c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Employees are allowed to cancel their own leave.
    op.drop_constraint(
        "ck_leave_request_canceller_valid",
        "leave_requests",
        type_="check",
    )

    # One allocation per leave request per calendar year.
    op.create_unique_constraint(
        "uq_leave_request_allocation_request_year",
        "leave_request_allocations",
        ["leave_request_id", "year"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_leave_request_allocation_request_year",
        "leave_request_allocations",
        type_="unique",
    )

    op.create_check_constraint(
        "ck_leave_request_canceller_valid",
        "leave_requests",
        "cancelled_by_id IS NULL OR cancelled_by_id <> user_id",
    )