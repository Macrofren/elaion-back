"""Repositório de acesso a dados de Tanque de Armazenamento do Terminal."""

from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import BicoTanqueVinculo, Tanque


def _tanque_options():
    """Carregamento ansioso das relações necessárias para TanqueResponseDTO."""
    return []


class TanqueRepository:
    """Operações de banco de dados para a entidade Tanque vinculada ao terminal."""

    async def get_by_id(self, session: AsyncSession, tanque_id: int) -> Optional[Tanque]:
        stmt = (
            select(Tanque)
            .options(*_tanque_options())
            .where(Tanque.id == tanque_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_terminal(
        self, session: AsyncSession, terminal_id: int, tanque_id: int
    ) -> Optional[Tanque]:
        stmt = (
            select(Tanque)
            .options(*_tanque_options())
            .where(
                Tanque.id == tanque_id,
                Tanque.terminal_id == terminal_id,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_identificador_terminal(
        self, session: AsyncSession, terminal_id: int, identificador: str
    ) -> Optional[Tanque]:
        stmt = (
            select(Tanque)
            .options(*_tanque_options())
            .where(
                Tanque.terminal_id == terminal_id,
                func.lower(Tanque.identificador_tanque) == identificador.strip().lower(),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_por_terminal(
        self,
        session: AsyncSession,
        terminal_id: int,
        apenas_ativos: bool = False,
        produto: Optional[str] = None,
    ) -> List[Tanque]:
        stmt = (
            select(Tanque)
            .options(*_tanque_options())
            .where(Tanque.terminal_id == terminal_id)
        )
        if apenas_ativos:
            stmt = stmt.where(Tanque.ativo.is_(True))
        if produto is not None:
            stmt = stmt.where(Tanque.produto == produto)

        stmt = stmt.order_by(Tanque.identificador_tanque.asc(), Tanque.id.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def salvar(self, session: AsyncSession, tanque: Tanque) -> Tanque:
        session.add(tanque)
        await session.flush()
        await session.refresh(tanque)
        return tanque

    async def excluir(self, session: AsyncSession, tanque: Tanque) -> None:
        await session.delete(tanque)
        await session.flush()

    async def tem_bicos_vinculados(self, session: AsyncSession, tanque_id: int) -> bool:
        stmt = select(func.count(BicoTanqueVinculo.bico_id)).where(
            BicoTanqueVinculo.tanque_id == tanque_id
        )
        result = await session.execute(stmt)
        count = result.scalar_one_or_none() or 0
        return count > 0


tanque_repository = TanqueRepository()
