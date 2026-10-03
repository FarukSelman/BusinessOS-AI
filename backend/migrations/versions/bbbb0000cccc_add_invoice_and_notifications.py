"""add_invoice_and_notifications

Revision ID: bbbb0000cccc
Revises: 9154920d66f8
Create Date: 2026-07-31 17:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'bbbb0000cccc'
down_revision: Union[str, Sequence[str], None] = 'b7f13a2c9e01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('invoices',
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('customer_id', sa.UUID(), nullable=True),
    sa.Column('customer_name', sa.String(length=150), nullable=False),
    sa.Column('customer_email', sa.String(length=255), nullable=True),
    sa.Column('appointment_id', sa.UUID(), nullable=True),
    sa.Column('invoice_number', sa.String(length=50), nullable=False),
    sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'SENT', 'PAID', 'OVERDUE', 'CANCELLED', name='invoicestatus'), nullable=False),
    sa.Column('payment_method', sa.Enum('CASH', 'CREDIT_CARD', 'BANK_TRANSFER', 'OTHER', name='paymentmethod'), nullable=True),
    sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ),
    sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('invoice_number')
    )
    op.create_table('notifications',
    sa.Column('business_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('type', sa.Enum('APPOINTMENT_CREATED', 'APPOINTMENT_CANCELLED', 'APPOINTMENT_COMPLETED', 'DOCUMENT_READY', 'DOCUMENT_FAILED', 'INVOICE_CREATED', 'INVOICE_PAID', 'TEAM_INVITATION', 'SYSTEM', name='notificationtype'), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('reference_id', sa.UUID(), nullable=True),
    sa.Column('reference_type', sa.String(length=50), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('notifications')
    op.drop_table('invoices')
    sa.Enum(name='notificationtype').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='invoicestatus').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='paymentmethod').drop(op.get_bind(), checkfirst=False)
