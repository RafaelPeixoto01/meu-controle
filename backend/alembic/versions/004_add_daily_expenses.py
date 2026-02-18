"""004: Add daily_expenses table (CR-005)

Revision ID: 004
Revises: 003
Create Date: 2026-02-17
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "daily_expenses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mes_referencia", sa.Date(), nullable=False),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("categoria", sa.String(50), nullable=False),
        sa.Column("subcategoria", sa.String(50), nullable=False),
        sa.Column("metodo_pagamento", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_daily_expenses_user_month",
        "daily_expenses",
        ["user_id", "mes_referencia"],
    )
    op.create_index(
        "ix_daily_expenses_data",
        "daily_expenses",
        ["data"],
    )


def downgrade():
    op.drop_index("ix_daily_expenses_data", table_name="daily_expenses")
    op.drop_index("ix_daily_expenses_user_month", table_name="daily_expenses")
    op.drop_table("daily_expenses")
