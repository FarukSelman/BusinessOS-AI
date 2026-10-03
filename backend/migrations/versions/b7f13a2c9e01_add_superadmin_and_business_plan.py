"""add_superadmin_and_business_plan

Revision ID: b7f13a2c9e01
Revises: 9154920d66f8
Create Date: 2026-07-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7f13a2c9e01'
down_revision: Union[str, Sequence[str], None] = '9154920d66f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# 1. PostgreSQL Enum nesnesini tanımlıyoruz
business_plan_enum = postgresql.ENUM('FREE', 'PRO', 'ENTERPRISE', name='business_plan')


def upgrade() -> None:
    """Upgrade schema."""
    # 2. Sütun eklemeden ÖNCE veritabanında ENUM tipini oluşturuyoruz
    business_plan_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        'users',
        sa.Column('is_superadmin', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        'businesses',
        sa.Column(
            'plan',
            business_plan_enum,
            nullable=False,
            server_default='FREE',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('businesses', 'plan')
    op.drop_column('users', 'is_superadmin')
    
    # 3. Geri alırken ENUM tipini de veritabanından siliyoruz
    business_plan_enum.drop(op.get_bind(), checkfirst=True)