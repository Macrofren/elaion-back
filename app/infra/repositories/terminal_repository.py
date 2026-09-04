"""Repositório de acesso a dados de Terminal."""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Terminal


class TerminalRepository:
    """Operações de banco da entidade Terminal (unidade operacional física)."""

    async def get_by_id(self, session: AsyncSession, terminal_id: int) -> Optional[Terminal]:
        stmt = select(Terminal).where(Terminal.id == terminal_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def criar(self, session: AsyncSession, dados: dict[str, Any]) -> Terminal:
        terminal = Terminal(**dados)
        session.add(terminal)
        await session.flush()
        return terminal


terminal_repository = TerminalRepository()
