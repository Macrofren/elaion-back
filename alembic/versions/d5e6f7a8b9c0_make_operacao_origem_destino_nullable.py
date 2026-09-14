"""make operacao_veiculo.origem_destino nullable

Substitui o ALTER TABLE que era executado em runtime no lifespan da aplicação
(anti-padrão) por uma migração Alembic versionada e idempotente no downgrade.

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-09-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "operacao_veiculo",
        "origem_destino",
        existing_type=sa.String(length=150),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "operacao_veiculo",
        "origem_destino",
        existing_type=sa.String(length=150),
        nullable=False,
    )
