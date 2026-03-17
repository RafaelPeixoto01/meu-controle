"""CR-032: Add analise_financeira table for AI financial analysis persistence.

Revision ID: 007
Revises: 006
Create Date: 2026-03-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "analise_financeira",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mes_referencia", sa.Date, nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False, server_default="mensal"),
        sa.Column("score_referencia", sa.Integer, nullable=False),
        sa.Column("dados_input", sa.Text, nullable=False),
        sa.Column("resultado", sa.Text, nullable=False),
        sa.Column("tokens_input", sa.Integer, nullable=True),
        sa.Column("tokens_output", sa.Integer, nullable=True),
        sa.Column("modelo", sa.String(50), nullable=False),
        sa.Column("tempo_processamento_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id", "mes_referencia", "tipo", name="uq_analise_user_month_tipo"
        ),
    )
    op.create_index(
        "ix_analise_user_month",
        "analise_financeira",
        ["user_id", "mes_referencia"],
    )


def downgrade() -> None:
    op.drop_index("ix_analise_user_month", table_name="analise_financeira")
    op.drop_table("analise_financeira")
