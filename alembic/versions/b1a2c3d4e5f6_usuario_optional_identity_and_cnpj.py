"""usuario optional identity fields and cnpj

Torna nome, sobrenome e cpf opcionais no usuario (master do terminal só tem razão
social; usuários informam CPF OU CNPJ) e adiciona a coluna cnpj (única, opcional).

Revision ID: b1a2c3d4e5f6
Revises: 88f3fba3a43c
Create Date: 2026-09-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, None] = "88f3fba3a43c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("usuario", "nome", existing_type=sa.String(length=100), nullable=True)
    op.alter_column("usuario", "sobrenome", existing_type=sa.String(length=100), nullable=True)
    op.alter_column("usuario", "cpf", existing_type=sa.String(length=11), nullable=True)
    op.add_column("usuario", sa.Column("cnpj", sa.String(length=14), nullable=True))
    op.create_index(op.f("ix_usuario_cnpj"), "usuario", ["cnpj"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_usuario_cnpj"), table_name="usuario")
    op.drop_column("usuario", "cnpj")
    op.alter_column("usuario", "cpf", existing_type=sa.String(length=11), nullable=False)
    op.alter_column("usuario", "sobrenome", existing_type=sa.String(length=100), nullable=False)
    op.alter_column("usuario", "nome", existing_type=sa.String(length=100), nullable=False)
