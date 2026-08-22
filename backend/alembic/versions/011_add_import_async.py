"""CR-052: Add erro_mensagem to import_batches (F07 — upload assincrono).

O upload passa a responder 202 com o lote em 'processando' e a extracao roda
em BackgroundTasks. A falha da IA, que antes se perdia na resposta HTTP, agora
fica registrada no proprio lote.

Os valores novos de `status` ('processando', 'erro') nao exigem alteracao de
schema: a coluna ja e String(20) e nao tem constraint de enum.

Revision ID: 011
Revises: 010
Create Date: 2026-08-22
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table: SQLite nao suporta ALTER em tabela com FK (CLAUDE.md)
    with op.batch_alter_table("import_batches") as batch_op:
        batch_op.add_column(sa.Column("erro_mensagem", sa.String(255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("import_batches") as batch_op:
        batch_op.drop_column("erro_mensagem")
