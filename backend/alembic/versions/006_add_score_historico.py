"""CR-026: Add score_historico table for financial health score persistence.

Revision ID: 006
Revises: 005
Create Date: 2026-03-16
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "score_historico",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mes_referencia", sa.Date, nullable=False),
        sa.Column("score_total", sa.Integer, nullable=False),
        sa.Column("d1_comprometimento", sa.Integer, nullable=False),
        sa.Column("d2_parcelas", sa.Integer, nullable=False),
        sa.Column("d3_poupanca", sa.Integer, nullable=False),
        sa.Column("d4_comportamento", sa.Integer, nullable=False),
        sa.Column("classificacao", sa.String(20), nullable=False),
        sa.Column("score_conservador", sa.Integer, nullable=True),
        sa.Column("dados_snapshot", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "mes_referencia", name="uq_score_user_month"),
    )
    op.create_index(
        "ix_score_historico_user_month",
        "score_historico",
        ["user_id", "mes_referencia"],
    )


def downgrade() -> None:
    op.drop_index("ix_score_historico_user_month", table_name="score_historico")
    op.drop_table("score_historico")
