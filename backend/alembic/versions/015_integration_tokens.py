"""CR-058: Tokens de integracao para o Lumi (RF-22, RN-054, ADR-023).

Cria `integration_tokens`: um token por linha, gravado so como hash SHA-256,
com o prefixo para identificar na lista e a revogacao. Tabela nova, sem
backfill; apagar o usuario apaga os tokens.

Revision ID: 015
Revises: 014
Create Date: 2026-10-23
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "integration_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("prefix", sa.String(8), nullable=False),
        # SHA-256 em hexadecimal; o token em si nunca e gravado
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_integration_tokens_user_id", "integration_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_integration_tokens_user_id", table_name="integration_tokens")
    op.drop_table("integration_tokens")
