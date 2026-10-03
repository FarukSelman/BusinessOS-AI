"""faz8_business_hours

Adds weekly business/branch opening hours and lets schedule blocks
target a single branch.

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-10-03 23:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d6'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. business_hours
    op.create_table(
        'business_hours',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('open_time', sa.Time(), nullable=True),
        sa.Column('close_time', sa.Time(), nullable=True),
        sa.Column('is_closed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.CheckConstraint('day_of_week BETWEEN 0 AND 6', name='ck_business_hours_day_of_week'),
        sa.CheckConstraint(
            'is_closed OR (open_time IS NOT NULL AND close_time IS NOT NULL AND open_time < close_time)',
            name='ck_business_hours_open_before_close',
        ),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_business_hours_business_day', 'business_hours', ['business_id', 'day_of_week'],
        unique=True, postgresql_where=sa.text('branch_id IS NULL'),
    )
    op.create_index(
        'uq_business_hours_branch_day', 'business_hours', ['branch_id', 'day_of_week'],
        unique=True, postgresql_where=sa.text('branch_id IS NOT NULL'),
    )

    # 2. schedule_blocks.branch_id (NULL = applies to the whole business)
    op.add_column('schedule_blocks', sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        'fk_schedule_blocks_branch_id', 'schedule_blocks', 'branches',
        ['branch_id'], ['id'], ondelete='CASCADE',
    )
    op.create_index('ix_schedule_blocks_branch_id', 'schedule_blocks', ['branch_id'])


def downgrade() -> None:
    op.drop_index('ix_schedule_blocks_branch_id', table_name='schedule_blocks')
    op.drop_constraint('fk_schedule_blocks_branch_id', 'schedule_blocks', type_='foreignkey')
    op.drop_column('schedule_blocks', 'branch_id')

    op.drop_index('uq_business_hours_branch_day', table_name='business_hours')
    op.drop_index('uq_business_hours_business_day', table_name='business_hours')
    op.drop_table('business_hours')
