"""CR-016: Add categoria and subcategoria to expenses table.

Revision ID: 005
Revises: 004
Create Date: 2026-03-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.add_column(sa.Column("categoria", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("subcategoria", sa.String(50), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.drop_column("subcategoria")
        batch_op.drop_column("categoria")
