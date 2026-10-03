"""faz9_reminder_delivery

Delivery bookkeeping for appointment reminders:
- reminder_logs.appointment_start / attempts / recipient_email
- unique (appointment_id, reminder_config_id, appointment_start): at most one
  reminder per appointment, config and start time
- SKIPPED value for reminderstatus

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-10-04 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # New enum values cannot be used in the same transaction on older
    # PostgreSQL versions; the autocommit block makes this safe everywhere.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE reminderstatus ADD VALUE IF NOT EXISTS 'SKIPPED'")

    op.add_column('reminder_logs', sa.Column('appointment_start', sa.DateTime(), nullable=True))
    op.add_column('reminder_logs', sa.Column('recipient_email', sa.Text(), nullable=True))
    op.add_column('reminder_logs', sa.Column('attempts', sa.Integer(), server_default='0', nullable=False))

    # Backfill rows written before this migration (normally none: nothing sent reminders yet).
    op.execute("""
        UPDATE reminder_logs AS l
        SET appointment_start = a.appointment_date + a.start_time
        FROM appointments AS a
        WHERE a.id = l.appointment_id AND l.appointment_start IS NULL
    """)
    op.execute("UPDATE reminder_logs SET appointment_start = created_at WHERE appointment_start IS NULL")
    op.alter_column('reminder_logs', 'appointment_start', nullable=False)

    # Keep only one row per key before adding the constraint (prefer a SENT
    # row, then the oldest; id breaks ties when created_at is identical).
    op.execute("""
        DELETE FROM reminder_logs
        WHERE id IN (
            SELECT id FROM (
                SELECT id, ROW_NUMBER() OVER (
                    PARTITION BY appointment_id, reminder_config_id, appointment_start
                    ORDER BY (status = 'SENT') DESC, created_at, id
                ) AS rn
                FROM reminder_logs
            ) ranked
            WHERE ranked.rn > 1
        )
    """)
    op.create_unique_constraint(
        'uq_reminder_logs_appointment_config_start',
        'reminder_logs',
        ['appointment_id', 'reminder_config_id', 'appointment_start'],
    )
    op.create_index('ix_reminder_logs_business_created', 'reminder_logs', ['business_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_reminder_logs_business_created', table_name='reminder_logs')
    op.drop_constraint('uq_reminder_logs_appointment_config_start', 'reminder_logs', type_='unique')
    op.drop_column('reminder_logs', 'attempts')
    op.drop_column('reminder_logs', 'recipient_email')
    op.drop_column('reminder_logs', 'appointment_start')
    # PostgreSQL cannot drop a single enum value; SKIPPED stays in reminderstatus.
    op.execute("UPDATE reminder_logs SET status = 'FAILED' WHERE status = 'SKIPPED'")
