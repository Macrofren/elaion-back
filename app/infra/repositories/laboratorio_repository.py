"""Repositório de acesso a dados de Laboratório do Terminal."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Laboratorio


class LaboratorioRepository:
    """Operações de banco de dados para a entidade Laboratorio vinculada ao terminal."""

    async def get_by_id(self, session: AsyncSession, lab_id: int) -> Optional[Laboratorio]:
        stmt = select(Laboratorio).where(Laboratorio.id == lab_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_terminal(
        self, session: AsyncSession, terminal_id: int, lab_id: int
    ) -> Optional[Laboratorio]:
        stmt = select(Laboratorio).where(
            Laboratorio.id == lab_id,
            Laboratorio.terminal_id == terminal_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_nome_terminal(
        self, session: AsyncSession, terminal_id: int, nome: str
    ) -> Optional[Laboratorio]:
        stmt = select(Laboratorio).where(
            Laboratorio.terminal_id == terminal_id,
            Laboratorio.nome.ilike(nome.strip()),
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_por_terminal(
        self,
        session: AsyncSession,
        terminal_id: int,
        apenas_ativos: bool = False,
    ) -> List[Laboratorio]:
        stmt = select(Laboratorio).where(Laboratorio.terminal_id == terminal_id)
        if apenas_ativos:
            stmt = stmt.where(Laboratorio.ativo.is_(True))
        stmt = stmt.order_by(Laboratorio.nome.asc(), Laboratorio.id.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def salvar(self, session: AsyncSession, lab: Laboratorio) -> Laboratorio:
        session.add(lab)
        await session.flush()
        await session.refresh(lab)
        return lab

    async def excluir(self, session: AsyncSession, lab: Laboratorio) -> None:
        await session.delete(lab)
        await session.flush()


laboratorio_repository = LaboratorioRepository()
