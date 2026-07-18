"""create invitations table

Revision ID: 50076394f750
Revises: 59d7aa989315
Create Date: 2026-07-16 17:12:14.324369
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "50076394f750"
down_revision: Union[str, Sequence[str], None] = "59d7aa989315"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


membership_role = postgresql.ENUM(
    "OWNER",
    "ADMIN",
    "EMPLOYEE",
    "VIEWER",
    name="membership_role",
    create_type=False,   # Enum zaten mevcut
)

invitation_status = postgresql.ENUM(
    "PENDING",
    "ACCEPTED",
    "REJECTED",
    "EXPIRED",
    name="invitation_status",
    create_type=False,
)


def upgrade() -> None:
    """Upgrade schema."""

    invitation_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "invitations",

        sa.Column(
            "business_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "email",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "role",
            membership_role,
            nullable=False,
        ),

        sa.Column(
            "token",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "status",
            invitation_status,
            nullable=False,
        ),

        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "accepted_at",
            sa.DateTime(),
            nullable=True,
        ),

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["business_id"],
            ["businesses.id"],
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint("token"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("invitations")

    invitation_status.drop(
        op.get_bind(),
        checkfirst=True,
    )