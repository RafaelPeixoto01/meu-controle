"""002: Add users and auth tables (CR-002)

Revision ID: 002
Revises: 001
Create Date: 2026-02-09
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Criar tabela users
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # 2. Criar tabela refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # 3. Clean slate: apagar dados existentes (sem user_id nao podem ser associados)
    op.execute("DELETE FROM expenses")
    op.execute("DELETE FROM incomes")

    # 4-6. Usar batch mode para SQLite: recriar tabelas com user_id FK + novos indices
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.drop_index("ix_expenses_mes_referencia")
        batch_op.add_column(sa.Column("user_id", sa.String(36), nullable=False))
        batch_op.create_foreign_key(
            "fk_expenses_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )
        batch_op.create_index("ix_expenses_user_month", ["user_id", "mes_referencia"])

    with op.batch_alter_table("incomes") as batch_op:
        batch_op.drop_index("ix_incomes_mes_referencia")
        batch_op.add_column(sa.Column("user_id", sa.String(36), nullable=False))
        batch_op.create_foreign_key(
            "fk_incomes_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE"
        )
        batch_op.create_index("ix_incomes_user_month", ["user_id", "mes_referencia"])


def downgrade():
    with op.batch_alter_table("incomes") as batch_op:
        batch_op.drop_index("ix_incomes_user_month")
        batch_op.drop_constraint("fk_incomes_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")
        batch_op.create_index("ix_incomes_mes_referencia", ["mes_referencia"])

    with op.batch_alter_table("expenses") as batch_op:
        batch_op.drop_index("ix_expenses_user_month")
        batch_op.drop_constraint("fk_expenses_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")
        batch_op.create_index("ix_expenses_mes_referencia", ["mes_referencia"])

    op.drop_table("refresh_tokens")
    op.drop_table("users")
