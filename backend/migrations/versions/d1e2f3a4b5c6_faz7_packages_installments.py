"""faz7_packages_installments

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-08-17 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create Enums
    sa.Enum('ACTIVE', 'INACTIVE', 'ARCHIVED', name='package_status_enum').create(op.get_bind())
    sa.Enum('ACTIVE', 'COMPLETED', 'EXPIRED', 'CANCELLED', name='customer_package_status_enum').create(op.get_bind())
    sa.Enum('PENDING', 'COMPLETED', 'CANCELLED', 'NO_SHOW', name='session_status_enum').create(op.get_bind())
    sa.Enum('PENDING', 'PAID', 'OVERDUE', 'CANCELLED', name='installment_status_enum').create(op.get_bind())
    
    # 2. Create service_packages table
    op.create_table(
        'service_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('services', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('total_sessions', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('discount_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('validity_days', sa.Integer(), nullable=False),
        sa.Column('is_installment_allowed', sa.Boolean(), nullable=False),
        sa.Column('max_installments', sa.Integer(), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'INACTIVE', 'ARCHIVED', name='package_status_enum', create_type=False), nullable=False),
        
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 3. Create customer_packages table
    op.create_table(
        'customer_packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('package_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('purchased_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_sessions', sa.Integer(), nullable=False),
        sa.Column('used_sessions', sa.Integer(), nullable=False),
        sa.Column('remaining_sessions', sa.Integer(), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('paid_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('status', postgresql.ENUM('ACTIVE', 'COMPLETED', 'EXPIRED', 'CANCELLED', name='customer_package_status_enum', create_type=False), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['package_id'], ['service_packages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 4. Create package_sessions table
    op.create_table(
        'package_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        
        sa.Column('customer_package_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_number', sa.Integer(), nullable=False),
        sa.Column('session_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'COMPLETED', 'CANCELLED', 'NO_SHOW', name='session_status_enum', create_type=False), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['completed_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['customer_package_id'], ['customer_packages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 5. Create installments table
    op.create_table(
        'installments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        
        sa.Column('customer_package_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('installment_number', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'PAID', 'OVERDUE', 'CANCELLED', name='installment_status_enum', create_type=False), nullable=False),
        sa.Column('payment_method', postgresql.ENUM('CASH', 'CREDIT_CARD', 'BANK_TRANSFER', 'OTHER', name='paymentmethod', create_type=False), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_package_id'], ['customer_packages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('installments')
    op.drop_table('package_sessions')
    op.drop_table('customer_packages')
    op.drop_table('service_packages')
    
    sa.Enum(name='installment_status_enum').drop(op.get_bind())
    sa.Enum(name='session_status_enum').drop(op.get_bind())
    sa.Enum(name='customer_package_status_enum').drop(op.get_bind())
    sa.Enum(name='package_status_enum').drop(op.get_bind())
