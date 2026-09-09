"""Repositório de acesso a dados de Terminal."""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Bico, BicoTanqueVinculo, Tanque, Terminal


class TerminalRepository:
    """Operações de banco da entidade Terminal (unidade operacional física)."""

    async def get_by_id(self, session: AsyncSession, terminal_id: int) -> Optional[Terminal]:
        stmt = (
            select(Terminal)
            .options(
                selectinload(Terminal.plataformas),
                selectinload(Terminal.tanques),
                selectinload(Terminal.bicos).selectinload(Bico.plataforma),
                selectinload(Terminal.bicos)
                .selectinload(Bico.vinculos_tanques)
                .selectinload(BicoTanqueVinculo.tanque),
            )
            .where(Terminal.id == terminal_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codigo_org(
        self, session: AsyncSession, organizacao_id: int, codigo_terminal: str
    ) -> Optional[Terminal]:
        stmt = select(Terminal).where(
            Terminal.organizacao_id == organizacao_id,
            Terminal.codigo_terminal == codigo_terminal,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def criar(self, session: AsyncSession, dados: dict[str, Any]) -> Terminal:
        terminal = Terminal(**dados)
        session.add(terminal)
        await session.flush()
        return terminal


    async def atualizar(
        self, session: AsyncSession, terminal: Terminal, dados: dict[str, Any]
    ) -> Terminal:
        for campo, valor in dados.items():
            if hasattr(terminal, campo) and valor is not None:
                setattr(terminal, campo, valor)
        await session.flush()
        await session.refresh(terminal)
        return terminal


terminal_repository = TerminalRepository()
