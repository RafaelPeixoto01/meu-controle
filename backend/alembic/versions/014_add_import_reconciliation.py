"""CR-057: Reconciliacao de total do documento na importacao (F07 — E-D, segunda metade).

Adiciona em `import_batches` o total de debitos impresso no documento e a soma
dos debitos que a extracao de fato produziu; em `import_transactions`, a
direcao da transacao (`debito`/`credito`), sem a qual nenhuma soma do lote e
comparavel com o documento (estornos e receitas tambem chegam com valor positivo).

Tudo nullable: nulo = lote anterior ao CR-057, sem conferencia. Sem backfill.

Revision ID: 014
Revises: 013
Create Date: 2026-09-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table: SQLite nao suporta ALTER em tabela com FK (CLAUDE.md)
    with op.batch_alter_table("import_batches") as batch_op:
        batch_op.add_column(sa.Column("total_debitos_documento", sa.Numeric(12, 2), nullable=True))
        batch_op.add_column(sa.Column("total_debitos_extraido", sa.Numeric(12, 2), nullable=True))

    with op.batch_alter_table("import_transactions") as batch_op:
        batch_op.add_column(sa.Column("natureza", sa.String(10), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("import_transactions") as batch_op:
        batch_op.drop_column("natureza")

    with op.batch_alter_table("import_batches") as batch_op:
        batch_op.drop_column("total_debitos_extraido")
        batch_op.drop_column("total_debitos_documento")
