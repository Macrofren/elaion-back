"""create congenere_produto table with combustivel enum

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-08 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "congenere_produto",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("congenere_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "combustivel",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column("aditivado", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("cor", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["congenere_id"], ["congenere.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("congenere_id", "combustivel", name="uq_congenere_combustivel"),
    )
    op.create_index(op.f("ix_congenere_produto_congenere_id"), "congenere_produto", ["congenere_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_congenere_produto_congenere_id"), table_name="congenere_produto")
    op.drop_table("congenere_produto")
