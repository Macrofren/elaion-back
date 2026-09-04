"""Repositório de acesso a dados de Organizacao."""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Organizacao


class OrganizacaoRepository:
    """Operações de banco da entidade Organizacao (empresa dona da conta SaaS)."""

    async def get_by_cnpj(self, session: AsyncSession, cnpj: str) -> Optional[Organizacao]:
        stmt = select(Organizacao).where(Organizacao.cnpj == cnpj)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def criar(
        self,
        session: AsyncSession,
        *,
        razao_social: str,
        nome_fantasia: str,
        cnpj: str,
    ) -> Organizacao:
        organizacao = Organizacao(
            razao_social=razao_social,
            nome_fantasia=nome_fantasia,
            cnpj=cnpj,
        )
        session.add(organizacao)
        await session.flush()
        return organizacao


organizacao_repository = OrganizacaoRepository()
