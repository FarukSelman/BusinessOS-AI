"""change embedding dimension to 1536

Revision ID: 2433ac3de27b
Revises: da53dd84a346
Create Date: 2026-07-24 13:50:27.652796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import VECTOR


# revision identifiers, used by Alembic.
revision: str = '2433ac3de27b'
down_revision: Union[str, Sequence[str], None] = 'da53dd84a346'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'document_chunks',
        'embedding',
        existing_type=VECTOR(dim=768),
        type_=VECTOR(dim=1536),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        'document_chunks',
        'embedding',
        existing_type=VECTOR(dim=1536),
        type_=VECTOR(dim=768),
        existing_nullable=True,
    )
