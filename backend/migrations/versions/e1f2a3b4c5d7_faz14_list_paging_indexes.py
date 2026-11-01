"""faz14_list_paging_indexes

Indexes for the paged customer, invoice and expense lists. Invoices and
expenses had no business_id index at all.

Revision ID: e1f2a3b4c5d7
Revises: d0e1f2a3b4c5
Create Date: 2026-11-01 15:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e1f2a3b4c5d7'
down_revision = 'd0e1f2a3b4c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_customers_business_created', 'customers', ['business_id', 'created_at'])
    op.create_index('ix_invoices_business_created', 'invoices', ['business_id', 'created_at'])
    op.create_index('ix_expenses_business_date', 'expenses', ['business_id', 'transaction_date'])


def downgrade() -> None:
    op.drop_index('ix_expenses_business_date', table_name='expenses')
    op.drop_index('ix_invoices_business_created', table_name='invoices')
    op.drop_index('ix_customers_business_created', table_name='customers')
