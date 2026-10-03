"""Faz 6 - Products & Stock

Revision ID: c1d2e3f4a5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-08-17 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b1c2d3e4f5a6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Enum creation
    op.execute("CREATE TYPE productstatus AS ENUM ('ACTIVE', 'INACTIVE', 'OUT_OF_STOCK');")
    op.execute("CREATE TYPE stockmovementtype AS ENUM ('PURCHASE', 'SALE', 'ADJUSTMENT', 'RETURN', 'TRANSFER', 'WASTE');")

    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sku', sa.String(length=50), nullable=True),
        sa.Column('barcode', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('brand', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=False),
        sa.Column('purchase_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('sale_price', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('current_stock', sa.Integer(), nullable=False),
        sa.Column('min_stock_level', sa.Integer(), nullable=False),
        sa.Column('max_stock_level', sa.Integer(), nullable=True),
        sa.Column('image_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'stock_movements',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('movement_type', sa.String(length=50), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('total_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'product_sales',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sale_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('items', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('subtotal', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['invoice_id'], ['invoices.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('product_sales')
    op.drop_table('stock_movements')
    op.drop_table('products')
    op.execute("DROP TYPE stockmovementtype;")
    op.execute("DROP TYPE productstatus;")
