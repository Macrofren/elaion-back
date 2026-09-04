"""Repositório de acesso a dados de ConviteCadastro (código de assinatura comercial)."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ConviteCadastro


class ConviteRepository:
    """Operações de banco relacionadas ao código de assinatura (convite_cadastro)."""

    async def get_by_codigo(self, session: AsyncSession, codigo: str) -> Optional[ConviteCadastro]:
        stmt = select(ConviteCadastro).where(ConviteCadastro.codigo == codigo)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def marcar_utilizado(
        self,
        session: AsyncSession,
        convite: ConviteCadastro,
        organizacao_id: int,
    ) -> ConviteCadastro:
        convite.utilizado = True
        convite.utilizado_em = datetime.now(timezone.utc)
        convite.organizacao_id = organizacao_id
        session.add(convite)
        await session.flush()
        return convite


convite_repository = ConviteRepository()
