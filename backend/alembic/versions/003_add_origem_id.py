"""003: Add origem_id for incremental replication (RF-06 fix)

Revision ID: 003
Revises: 002
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar origem_id para rastrear replicacao entre meses
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.add_column(
            sa.Column("origem_id", sa.String(36), nullable=True)
        )
        batch_op.create_index("ix_expenses_origem_id", ["origem_id"])

    with op.batch_alter_table("incomes") as batch_op:
        batch_op.add_column(
            sa.Column("origem_id", sa.String(36), nullable=True)
        )
        batch_op.create_index("ix_incomes_origem_id", ["origem_id"])


def downgrade():
    with op.batch_alter_table("incomes") as batch_op:
        batch_op.drop_index("ix_incomes_origem_id")
        batch_op.drop_column("origem_id")

    with op.batch_alter_table("expenses") as batch_op:
        batch_op.drop_index("ix_expenses_origem_id")
        batch_op.drop_column("origem_id")
