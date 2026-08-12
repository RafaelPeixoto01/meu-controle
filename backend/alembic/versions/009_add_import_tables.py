"""CR-046: Add import_batches and import_transactions tables (F07 — importacao de extratos).

Revision ID: 009
Revises: 008
Create Date: 2026-08-12
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("banco_detectado", sa.String(50), nullable=True),
        sa.Column("tipo_documento", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pendente_revisao"),
        sa.Column("tokens_input", sa.Integer, nullable=True),
        sa.Column("tokens_output", sa.Integer, nullable=True),
        sa.Column("modelo", sa.String(50), nullable=False),
        sa.Column("tempo_processamento_ms", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_import_batches_user_status",
        "import_batches",
        ["user_id", "status"],
    )

    op.create_table(
        "import_transactions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "batch_id",
            sa.String(36),
            sa.ForeignKey("import_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("data", sa.Date, nullable=False),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("classificacao", sa.String(20), nullable=False),
        sa.Column("motivo_ignorar", sa.String(255), nullable=True),
        sa.Column("expense_id_sugerido", sa.String(36), nullable=True),
        sa.Column("categoria", sa.String(50), nullable=True),
        sa.Column("subcategoria", sa.String(50), nullable=True),
        sa.Column("metodo_pagamento", sa.String(30), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pendente"),
        sa.Column("daily_expense_id_criado", sa.String(36), nullable=True),
        sa.Column("expense_id_atualizado", sa.String(36), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_import_transactions_batch_id",
        "import_transactions",
        ["batch_id"],
    )
    op.create_index(
        "ix_import_tx_user_fingerprint",
        "import_transactions",
        ["user_id", "fingerprint"],
    )


def downgrade() -> None:
    op.drop_index("ix_import_tx_user_fingerprint", table_name="import_transactions")
    op.drop_index("ix_import_transactions_batch_id", table_name="import_transactions")
    op.drop_table("import_transactions")
    op.drop_index("ix_import_batches_user_status", table_name="import_batches")
    op.drop_table("import_batches")
