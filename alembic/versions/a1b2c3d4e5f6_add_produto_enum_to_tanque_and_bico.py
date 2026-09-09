"""add produto enum to tanque and bico and make produto_id nullable

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-09-09 11:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Adiciona coluna 'produto' em tanque
    op.add_column(
        "tanque",
        sa.Column(
            "produto",
            sa.String(length=50),
            server_default=sa.text("'DIESEL_S10_A'"),
            nullable=False,
        ),
    )
    # 2. Torna produto_id opcional em tanque
    op.alter_column(
        "tanque",
        "produto_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )

    # 3. Adiciona coluna 'produto' em bico
    op.add_column(
        "bico",
        sa.Column(
            "produto",
            sa.String(length=50),
            server_default=sa.text("'DIESEL_S10_A'"),
            nullable=False,
        ),
    )
    # 4. Torna produto_id opcional em bico
    op.alter_column(
        "bico",
        "produto_id",
        existing_type=sa.BigInteger(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "bico",
        "produto_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.drop_column("bico", "produto")

    op.alter_column(
        "tanque",
        "produto_id",
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.drop_column("tanque", "produto")
