"""Repositório de acesso a dados de Plataforma de Operação do Terminal."""

from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Bico, Plataforma, TipoPlataforma


class PlataformaRepository:
    """Operações de banco de dados para a entidade Plataforma vinculada ao terminal."""

    async def get_by_id(self, session: AsyncSession, plataforma_id: int) -> Optional[Plataforma]:
        stmt = select(Plataforma).where(Plataforma.id == plataforma_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_terminal(
        self, session: AsyncSession, terminal_id: int, plataforma_id: int
    ) -> Optional[Plataforma]:
        stmt = select(Plataforma).where(
            Plataforma.id == plataforma_id,
            Plataforma.terminal_id == terminal_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_identificador_terminal(
        self, session: AsyncSession, terminal_id: int, identificador: str
    ) -> Optional[Plataforma]:
        stmt = select(Plataforma).where(
            Plataforma.terminal_id == terminal_id,
            func.lower(Plataforma.identificador) == identificador.strip().lower(),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_por_terminal(
        self,
        session: AsyncSession,
        terminal_id: int,
        apenas_ativos: bool = False,
        tipo: Optional[TipoPlataforma] = None,
    ) -> List[Plataforma]:
        stmt = select(Plataforma).where(Plataforma.terminal_id == terminal_id)
        if apenas_ativos:
            stmt = stmt.where(Plataforma.ativo.is_(True))
        if tipo is not None:
            stmt = stmt.where(Plataforma.tipo == tipo)
        stmt = stmt.order_by(Plataforma.identificador.asc(), Plataforma.id.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def salvar(self, session: AsyncSession, plataforma: Plataforma) -> Plataforma:
        session.add(plataforma)
        await session.flush()
        await session.refresh(plataforma)
        return plataforma

    async def excluir(self, session: AsyncSession, plataforma: Plataforma) -> None:
        await session.delete(plataforma)
        await session.flush()

    async def tem_bicos_vinculados(self, session: AsyncSession, plataforma_id: int) -> bool:
        stmt = select(func.count(Bico.id)).where(Bico.plataforma_id == plataforma_id)
        result = await session.execute(stmt)
        count = result.scalar_one_or_none() or 0
        return count > 0


plataforma_repository = PlataformaRepository()
