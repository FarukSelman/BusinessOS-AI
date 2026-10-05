"""faz10_turkish_booking_note

Appointments booked on the public page carried an English note
("Booked via public booking page"); the app is Turkish.

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-10-05 19:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a7b8c9d0e1f2'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None

OLD = "Booked via public booking page"
NEW = "Online randevu sayfasından alındı."


def upgrade() -> None:
    op.execute(
        sa.text("UPDATE appointments SET notes = :new WHERE notes = :old").bindparams(new=NEW, old=OLD)
    )


def downgrade() -> None:
    op.execute(
        sa.text("UPDATE appointments SET notes = :old WHERE notes = :new").bindparams(new=NEW, old=OLD)
    )
