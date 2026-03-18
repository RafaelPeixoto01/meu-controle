"""CR-033: Add alerta_estado and configuracao_alertas tables for intelligent alerts.

Revision ID: 008
Revises: 007
Create Date: 2026-03-18
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerta_estado",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("alerta_tipo", sa.String(10), nullable=False),
        sa.Column("alerta_referencia", sa.String(100), nullable=False),
        sa.Column("mes_referencia", sa.Date, nullable=False),
        sa.Column("severidade", sa.String(20), nullable=False),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("descricao", sa.String(500), nullable=True),
        sa.Column("dados_extra", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ativo"),
        sa.Column("contexto_aba", sa.String(30), nullable=False),
        sa.Column("acao_tipo", sa.String(30), nullable=True),
        sa.Column("acao_referencia_id", sa.String(36), nullable=True),
        sa.Column("acao_destino", sa.String(100), nullable=True),
        sa.Column("impacto_mensal", sa.Numeric(12, 2), nullable=True),
        sa.Column("impacto_anual", sa.Numeric(12, 2), nullable=True),
        sa.Column("visto_em", sa.DateTime, nullable=True),
        sa.Column("dispensado_em", sa.DateTime, nullable=True),
        sa.Column("resolvido_em", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "user_id", "alerta_tipo", "alerta_referencia", "mes_referencia",
            name="uq_alerta_user_tipo_ref_mes",
        ),
    )
    op.create_index(
        "ix_alerta_user_status",
        "alerta_estado",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_alerta_user_mes",
        "alerta_estado",
        ["user_id", "mes_referencia"],
    )

    op.create_table(
        "configuracao_alertas",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("antecedencia_vencimento", sa.Integer, nullable=False, server_default="3"),
        sa.Column("alerta_atrasadas", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("alerta_parcelas_encerrando", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("alerta_score", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("alerta_comprometimento", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("limiar_comprometimento", sa.Integer, nullable=False, server_default="50"),
        sa.Column("alerta_parcela_ativada", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("alerta_ia", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("configuracao_alertas")
    op.drop_index("ix_alerta_user_mes", table_name="alerta_estado")
    op.drop_index("ix_alerta_user_status", table_name="alerta_estado")
    op.drop_table("alerta_estado")
