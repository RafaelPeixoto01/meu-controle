"""CR-049: Add installment fields to import_transactions (F07 — compras parceladas).

Revision ID: 010
Revises: 009
Create Date: 2026-08-16
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table: SQLite nao suporta ALTER em tabela com FK (CLAUDE.md)
    with op.batch_alter_table("import_transactions") as batch_op:
        batch_op.add_column(sa.Column("parcela_atual", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("parcela_total", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("expense_id_criado", sa.String(36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("import_transactions") as batch_op:
        batch_op.drop_column("expense_id_criado")
        batch_op.drop_column("parcela_total")
        batch_op.drop_column("parcela_atual")
