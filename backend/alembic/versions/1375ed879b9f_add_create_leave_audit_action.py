from typing import Sequence, Union

from alembic import op


revision: str = "1375ed879b9f" 
down_revision: Union[str, Sequence[str], None] = "6a6c76c584b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TYPE audit_action_enum "
        "ADD VALUE IF NOT EXISTS 'CREATE_LEAVE'"
    )


def downgrade() -> None:
    # PostgreSQL does not support removing a single enum value directly.
    pass