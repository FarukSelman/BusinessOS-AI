"""faz13_appointments_calendar_index

Index for the calendar view's date-range queries.

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-11-01 12:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd0e1f2a3b4c5'
down_revision = 'c9d0e1f2a3b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_appointments_business_date', 'appointments', ['business_id', 'appointment_date'])


def downgrade() -> None:
    op.drop_index('ix_appointments_business_date', table_name='appointments')
