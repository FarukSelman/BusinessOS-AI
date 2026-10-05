"""faz11_online_booking_settings

businesses.online_booking_auto_confirm: confirm online bookings
automatically (default: no, they arrive as PENDING).

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-10-05 19:50:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b8c9d0e1f2a3'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'businesses',
        sa.Column('online_booking_auto_confirm', sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column('businesses', 'online_booking_auto_confirm')
