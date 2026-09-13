"""update combustivel gasolina_a to gasolina_c in database

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-11 08:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Atualiza registros existentes que estejam com 'GASOLINA_A' para 'GASOLINA_C'
    op.execute(
        sa.text(
            "UPDATE congenere_produto SET combustivel = 'GASOLINA_C' WHERE combustivel = 'GASOLINA_A'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE tanque SET produto = 'GASOLINA_C' WHERE produto = 'GASOLINA_A'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE bico SET produto = 'GASOLINA_C' WHERE produto = 'GASOLINA_A'"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE congenere_produto SET combustivel = 'GASOLINA_A' WHERE combustivel = 'GASOLINA_C'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE tanque SET produto = 'GASOLINA_A' WHERE produto = 'GASOLINA_C'"
        )
    )
    op.execute(
        sa.text(
            "UPDATE bico SET produto = 'GASOLINA_A' WHERE produto = 'GASOLINA_C'"
        )
    )
