"""Repositório de acesso a dados de Usuario."""

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Usuario


class UsuarioRepository:
    """Operações de banco da entidade Usuario (colaboradores, master, congêneres)."""

    async def get_by_id(self, session: AsyncSession, usuario_id: int) -> Optional[Usuario]:
        stmt = select(Usuario).where(Usuario.id == usuario_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_cpf(self, session: AsyncSession, cpf: str) -> Optional[Usuario]:
        stmt = select(Usuario).where(Usuario.cpf == cpf)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_cnpj(self, session: AsyncSession, cnpj: str) -> Optional[Usuario]:
        stmt = select(Usuario).where(Usuario.cnpj == cnpj)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[Usuario]:
        stmt = select(Usuario).where(Usuario.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_codigo_ativacao(
        self, session: AsyncSession, cpf: str, codigo_ativacao: str
    ) -> Optional[Usuario]:
        stmt = select(Usuario).where(
            Usuario.cpf == cpf,
            Usuario.codigo_ativacao == codigo_ativacao,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def codigo_ativacao_existe(self, session: AsyncSession, codigo: str) -> bool:
        stmt = select(Usuario.id).where(Usuario.codigo_ativacao == codigo)
        result = await session.execute(stmt)
        return result.first() is not None

    async def codigo_liberacao_existe(self, session: AsyncSession, codigo: str) -> bool:
        stmt = select(Usuario.id).where(Usuario.codigo_liberacao_master == codigo)
        result = await session.execute(stmt)
        return result.first() is not None

    async def criar(self, session: AsyncSession, dados: dict[str, Any]) -> Usuario:
        usuario = Usuario(**dados)
        session.add(usuario)
        await session.flush()
        return usuario

    async def salvar(self, session: AsyncSession, usuario: Usuario) -> Usuario:
        session.add(usuario)
        await session.flush()
        return usuario


usuario_repository = UsuarioRepository()
