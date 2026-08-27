"""CR-054: Memoria de categorizacao da importacao (F07 — item E-C do roadmap v2).

Cria `import_category_rules` (uma regra por padrao de descritor, por usuario,
aprendida no confirm) e adiciona `origem_sugestao` em `import_transactions`,
que sinaliza na revisao quando a sugestao veio da regra e nao do modelo.

`origem_sugestao` nasce NULL em todo o historico — nulo significa exatamente o
comportamento anterior (palpite da IA), entao nao ha backfill a fazer.

Revision ID: 012
Revises: 011
Create Date: 2026-08-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_category_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("padrao", sa.String(255), nullable=False),
        sa.Column("descricao_sugerida", sa.String(255), nullable=True),
        sa.Column("categoria", sa.String(50), nullable=True),
        sa.Column("subcategoria", sa.String(50), nullable=True),
        sa.Column("metodo_pagamento", sa.String(30), nullable=True),
        sa.Column("hits", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        # Chave do upsert e do lookup: a leitura sempre filtra por user_id
        sa.UniqueConstraint("user_id", "padrao", name="uq_import_rule_user_padrao"),
    )

    # batch_alter_table: SQLite nao suporta ALTER em tabela com FK (CLAUDE.md)
    with op.batch_alter_table("import_transactions") as batch_op:
        batch_op.add_column(sa.Column("origem_sugestao", sa.String(20), nullable=True))
        # Texto cru do documento: `descricao` pode ser reescrita por uma regra,
        # e o fingerprint (RN-042) e a realimentacao da memoria dependem do cru
        batch_op.add_column(sa.Column("descricao_original", sa.String(255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("import_transactions") as batch_op:
        batch_op.drop_column("descricao_original")
        batch_op.drop_column("origem_sugestao")

    op.drop_table("import_category_rules")
