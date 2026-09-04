"""Repositório de acesso a dados de UsuarioTerminal (vínculo usuário ↔ terminal)."""

from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Terminal, Usuario, UsuarioTerminal


class UsuarioTerminalRepository:
    """Operações de banco do vínculo de acesso do usuário a um terminal."""

    async def get_vinculo(
        self, session: AsyncSession, usuario_id: int, terminal_id: int
    ) -> Optional[UsuarioTerminal]:
        stmt = select(UsuarioTerminal).where(
            UsuarioTerminal.usuario_id == usuario_id,
            UsuarioTerminal.terminal_id == terminal_id,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_terminais_do_usuario(
        self, session: AsyncSession, usuario_id: int
    ) -> Sequence[UsuarioTerminal]:
        stmt = select(UsuarioTerminal).where(
            UsuarioTerminal.usuario_id == usuario_id,
            UsuarioTerminal.ativo.is_(True),
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def listar_terminais(
        self, session: AsyncSession, usuario_id: int
    ) -> List[Terminal]:
        """Retorna os Terminais ativos aos quais o usuário está vinculado."""
        stmt = (
            select(Terminal)
            .join(UsuarioTerminal, UsuarioTerminal.terminal_id == Terminal.id)
            .where(
                UsuarioTerminal.usuario_id == usuario_id,
                UsuarioTerminal.ativo.is_(True),
            )
            .order_by(Terminal.id)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def listar_usuarios_do_terminal(
        self, session: AsyncSession, terminal_id: int
    ) -> List[Usuario]:
        stmt = (
            select(Usuario)
            .join(UsuarioTerminal, UsuarioTerminal.usuario_id == Usuario.id)
            .where(UsuarioTerminal.terminal_id == terminal_id)
            .order_by(Usuario.id)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def criar_vinculo(
        self, session: AsyncSession, usuario_id: int, terminal_id: int
    ) -> UsuarioTerminal:
        vinculo = UsuarioTerminal(usuario_id=usuario_id, terminal_id=terminal_id, ativo=True)
        session.add(vinculo)
        await session.flush()
        return vinculo


usuario_terminal_repository = UsuarioTerminalRepository()
