"""Repositório de acesso a dados de permissões (catálogo e atribuição)."""

from typing import List, Sequence, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.domain.models import (
    ModuloAssinatura,
    ModuloFuncionalidade,
    TerminalModuloContratado,
    UsuarioPermissao,
    UsuarioTerminal,
)


class PermissaoRepository:
    """Operações de banco do catálogo de permissões e da atribuição a usuários."""

    async def listar_modulos_contratados(
        self, session: AsyncSession, terminal_id: int
    ) -> List[ModuloAssinatura]:
        """
        Retorna os módulos ativos contratados pelo terminal, com suas
        funcionalidades carregadas (para alimentar o Drawer de Novo Colaborador).
        """
        stmt = (
            select(ModuloAssinatura)
            .join(TerminalModuloContratado, TerminalModuloContratado.modulo_id == ModuloAssinatura.id)
            .where(
                TerminalModuloContratado.terminal_id == terminal_id,
                TerminalModuloContratado.ativo.is_(True),
                ModuloAssinatura.ativo.is_(True),
            )
            .options(selectinload(ModuloAssinatura.funcionalidades))
            .order_by(ModuloAssinatura.id)
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def resolver_funcionalidades(
        self, session: AsyncSession, identificadores: Sequence[Union[int, str]]
    ) -> List[ModuloFuncionalidade]:
        """
        Resolve uma lista de identificadores (IDs numéricos ou chaves textuais)
        para as entidades ModuloFuncionalidade correspondentes.
        """
        if not identificadores:
            return []

        ids: List[int] = []
        chaves: List[str] = []
        for item in identificadores:
            if isinstance(item, int) or (isinstance(item, str) and item.isdigit()):
                ids.append(int(item))
            else:
                chaves.append(str(item))

        condicoes = []
        if ids:
            condicoes.append(ModuloFuncionalidade.id.in_(ids))
        if chaves:
            condicoes.append(ModuloFuncionalidade.chave.in_(chaves))

        from sqlalchemy import or_

        stmt = select(ModuloFuncionalidade).where(or_(*condicoes))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def listar_funcionalidades_usuario(
        self, session: AsyncSession, usuario_id: int
    ) -> List[ModuloFuncionalidade]:
        """
        Retorna as funcionalidades permitidas do usuário (agregadas entre todos os
        seus terminais ativos), com o módulo carregado. Usado para montar as
        permissões no login/perfil.
        """
        stmt = (
            select(ModuloFuncionalidade)
            .join(UsuarioPermissao, UsuarioPermissao.funcionalidade_id == ModuloFuncionalidade.id)
            .join(UsuarioTerminal, UsuarioTerminal.id == UsuarioPermissao.usuario_terminal_id)
            .where(
                UsuarioTerminal.usuario_id == usuario_id,
                UsuarioTerminal.ativo.is_(True),
                UsuarioPermissao.permitido.is_(True),
            )
            .options(joinedload(ModuloFuncionalidade.modulo))
            .order_by(ModuloFuncionalidade.id)
        )
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def atribuir_permissoes(
        self,
        session: AsyncSession,
        usuario_terminal_id: int,
        funcionalidade_ids: Sequence[int],
    ) -> None:
        """Cria as linhas de UsuarioPermissao para o vínculo usuário↔terminal."""
        for funcionalidade_id in funcionalidade_ids:
            session.add(
                UsuarioPermissao(
                    usuario_terminal_id=usuario_terminal_id,
                    funcionalidade_id=funcionalidade_id,
                    permitido=True,
                )
            )
        await session.flush()


permissao_repository = PermissaoRepository()
