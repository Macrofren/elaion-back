"""add tipo_operacao to bico and make produto nullable

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-09 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adiciona coluna 'tipo_operacao' em bico
    op.add_column(
        "bico",
        sa.Column(
            "tipo_operacao",
            sa.String(length=30),
            server_default=sa.text("'CARREGAMENTO'"),
            nullable=False,
        ),
    )
    # 2. Torna produto opcional em bico
    op.alter_column(
        "bico",
        "produto",
        existing_type=sa.String(length=50),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "bico",
        "produto",
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.drop_column("bico", "tipo_operacao")
