"""Initial schema: expenses and incomes tables

Revision ID: 001
Revises: None
Create Date: 2026-02-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "expenses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mes_referencia", sa.Date(), nullable=False, index=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("vencimento", sa.Date(), nullable=False),
        sa.Column("parcela_atual", sa.Integer(), nullable=True),
        sa.Column("parcela_total", sa.Integer(), nullable=True),
        sa.Column("recorrente", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="Pendente"
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "incomes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("mes_referencia", sa.Date(), nullable=False, index=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("data", sa.Date(), nullable=True),
        sa.Column("recorrente", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("incomes")
    op.drop_table("expenses")
