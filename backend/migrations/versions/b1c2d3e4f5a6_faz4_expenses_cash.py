"""faz4 expenses cash

Revision ID: b1c2d3e4f5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-08-10 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Expense categories
    op.create_table(
        'expense_categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('color', sa.String(length=7), nullable=False, default='#ef4444'),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Enum types creation for expenses
    op.execute("CREATE TYPE transactiondirection AS ENUM ('INCOME', 'EXPENSE')")
    op.execute("CREATE TYPE expensestatus AS ENUM ('PENDING', 'PAID', 'CANCELLED')")
    op.execute("CREATE TYPE recurrencetype AS ENUM ('NONE', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY')")

    # Expenses
    op.create_table(
        'expenses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('direction', postgresql.ENUM('INCOME', 'EXPENSE', name='transactiondirection', create_type=False), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, default='TRY'),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('status', postgresql.ENUM('PENDING', 'PAID', 'CANCELLED', name='expensestatus', create_type=False), nullable=False),
        sa.Column('payment_method', postgresql.ENUM('CASH', 'CREDIT_CARD', 'BANK_TRANSFER', 'OTHER', name='paymentmethod', create_type=False), nullable=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('recurrence', postgresql.ENUM('NONE', 'DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', name='recurrencetype', create_type=False), nullable=False),
        sa.Column('is_auto_generated', sa.Boolean(), nullable=False, default=False),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['category_id'], ['expense_categories.id'], ),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Enum types for Cash Register
    op.execute("CREATE TYPE cashregisterstatus AS ENUM ('OPEN', 'CLOSED')")
    op.execute("CREATE TYPE cashtransactiontype AS ENUM ('OPENING', 'SALE', 'EXPENSE', 'DEPOSIT', 'WITHDRAWAL', 'CLOSING')")

    # Cash Registers
    op.create_table(
        'cash_registers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('opened_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('closed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('register_date', sa.Date(), nullable=False),
        sa.Column('opening_balance', sa.Numeric(precision=12, scale=2), nullable=False, default=0),
        sa.Column('closing_balance', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('expected_balance', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('difference', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('status', postgresql.ENUM('OPEN', 'CLOSED', name='cashregisterstatus', create_type=False), nullable=False),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ),
        sa.ForeignKeyConstraint(['opened_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['closed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', 'branch_id', 'register_date', name='uq_cash_register')
    )

    # Cash Transactions
    op.create_table(
        'cash_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('register_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('transaction_type', postgresql.ENUM('OPENING', 'SALE', 'EXPENSE', 'DEPOSIT', 'WITHDRAWAL', 'CLOSING', name='cashtransactiontype', create_type=False), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.ForeignKeyConstraint(['register_id'], ['cash_registers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('cash_transactions')
    op.drop_table('cash_registers')
    op.execute('DROP TYPE cashtransactiontype')
    op.execute('DROP TYPE cashregisterstatus')
    
    op.drop_table('expenses')
    op.execute('DROP TYPE recurrencetype')
    op.execute('DROP TYPE expensestatus')
    op.execute('DROP TYPE transactiondirection')

    op.drop_table('expense_categories')
