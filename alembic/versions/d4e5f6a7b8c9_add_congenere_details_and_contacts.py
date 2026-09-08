"""add congenere details and contacts

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-09-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Novas colunas em congenere
    op.add_column("congenere", sa.Column("inscricao_estadual", sa.String(length=30), nullable=True))
    op.add_column("congenere", sa.Column("telefone", sa.String(length=20), server_default="", nullable=False))
    op.add_column("congenere", sa.Column("email", sa.String(length=100), server_default="", nullable=False))
    op.add_column("congenere", sa.Column("telefone_financeiro", sa.String(length=20), nullable=True))
    op.add_column("congenere", sa.Column("email_financeiro", sa.String(length=100), nullable=True))
    op.add_column("congenere", sa.Column("cep", sa.String(length=8), nullable=True))
    op.add_column("congenere", sa.Column("logradouro", sa.String(length=150), nullable=True))
    op.add_column("congenere", sa.Column("numero", sa.String(length=20), nullable=True))
    op.add_column("congenere", sa.Column("complemento", sa.String(length=100), nullable=True))
    op.add_column("congenere", sa.Column("bairro", sa.String(length=100), nullable=True))
    op.add_column("congenere", sa.Column("cidade", sa.String(length=100), nullable=True))
    op.add_column("congenere", sa.Column("uf", sa.String(length=2), nullable=True))
    op.add_column("congenere", sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False))
    op.add_column("congenere", sa.Column("atualizado_em", sa.DateTime(timezone=True), nullable=True))

    # 2. Alterar cnpj para nullable=False e criar índice
    op.alter_column("congenere", "cnpj", existing_type=sa.String(length=14), nullable=False)
    op.create_index(op.f("ix_congenere_cnpj"), "congenere", ["cnpj"], unique=False)

    # 3. UniqueConstraint terminal_id + cnpj
    op.create_unique_constraint("uq_congenere_terminal_cnpj", "congenere", ["terminal_id", "cnpj"])


def downgrade() -> None:
    op.drop_constraint("uq_congenere_terminal_cnpj", "congenere", type_="unique")
    op.drop_index(op.f("ix_congenere_cnpj"), table_name="congenere")
    op.alter_column("congenere", "cnpj", existing_type=sa.String(length=14), nullable=True)
    op.drop_column("congenere", "atualizado_em")
    op.drop_column("congenere", "criado_em")
    op.drop_column("congenere", "uf")
    op.drop_column("congenere", "cidade")
    op.drop_column("congenere", "bairro")
    op.drop_column("congenere", "complemento")
    op.drop_column("congenere", "numero")
    op.drop_column("congenere", "logradouro")
    op.drop_column("congenere", "cep")
    op.drop_column("congenere", "email_financeiro")
    op.drop_column("congenere", "telefone_financeiro")
    op.drop_column("congenere", "email")
    op.drop_column("congenere", "telefone")
    op.drop_column("congenere", "inscricao_estadual")
