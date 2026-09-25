"""CR-056: Historico e desfazer da importacao (F07 — item E-D do roadmap v2).

Cria `import_effects`, o diario do que cada confirm gravou: uma linha por gasto
diario criado, por parcela criada e por planejado conciliado (com o status e o
valor anteriores). E a fonte da verdade do undo — os campos de auditoria das
transacoes nao bastam (so registram a parcela ancora da serie, e na RN-046
apontam para uma parcela que ja existia). Ver ADR-022.

Adiciona tambem `confirmado_em` e `revertido_em` em `import_batches`. Lote
confirmado antes deste CR fica com `confirmado_em` nulo: e o marcador de "sem
diario", que o impede de ser desfeito. Nao ha backfill possivel.

Revision ID: 013
Revises: 012
Create Date: 2026-09-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_effects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "batch_id",
            sa.String(36),
            sa.ForeignKey("import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            sa.String(36),
            sa.ForeignKey("import_transactions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # gasto_diario_criado | planejado_criado | planejado_conciliado
        sa.Column("tipo", sa.String(30), nullable=False),
        # Sem FK de proposito: aponta para daily_expenses OU expenses conforme o
        # tipo, e o usuario pode apagar o lancamento a qualquer momento
        sa.Column("entidade_id", sa.String(36), nullable=False),
        sa.Column("assinatura", sa.String(64), nullable=False),
        sa.Column("status_anterior", sa.String(20), nullable=True),
        sa.Column("valor_anterior", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_import_effects_batch", "import_effects", ["batch_id"])

    # batch_alter_table: SQLite nao suporta ALTER em tabela com FK (CLAUDE.md)
    with op.batch_alter_table("import_batches") as batch_op:
        batch_op.add_column(sa.Column("confirmado_em", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("revertido_em", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("import_batches") as batch_op:
        batch_op.drop_column("revertido_em")
        batch_op.drop_column("confirmado_em")

    op.drop_index("ix_import_effects_batch", table_name="import_effects")
    op.drop_table("import_effects")
