"""Repositório de acesso a dados de Bico de Operação e Manifolds do Terminal."""

from typing import List, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Bico, BicoTanqueVinculo


def _bico_options():
    """Carregamento ansioso das relações necessárias para compor o BicoResponseDTO."""
    return [
        selectinload(Bico.plataforma),
        selectinload(Bico.vinculos_tanques).selectinload(BicoTanqueVinculo.tanque),
    ]


class BicoRepository:
    """Operações de banco de dados para a entidade Bico vinculada ao terminal."""

    async def get_by_id(self, session: AsyncSession, bico_id: int) -> Optional[Bico]:
        stmt = (
            select(Bico)
            .options(*_bico_options())
            .where(Bico.id == bico_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_terminal(
        self, session: AsyncSession, terminal_id: int, bico_id: int
    ) -> Optional[Bico]:
        stmt = (
            select(Bico)
            .options(*_bico_options())
            .where(
                Bico.id == bico_id,
                Bico.terminal_id == terminal_id,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_identificador_terminal(
        self, session: AsyncSession, terminal_id: int, identificador: str
    ) -> Optional[Bico]:
        stmt = (
            select(Bico)
            .options(*_bico_options())
            .where(
                Bico.terminal_id == terminal_id,
                func.lower(Bico.identificador_bico) == identificador.strip().lower(),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_por_terminal(
        self,
        session: AsyncSession,
        terminal_id: int,
        apenas_ativos: bool = False,
        plataforma_id: Optional[int] = None,
        produto: Optional[str] = None,
        produto_id: Optional[int] = None,
    ) -> List[Bico]:
        stmt = (
            select(Bico)
            .options(*_bico_options())
            .where(Bico.terminal_id == terminal_id)
        )
        if apenas_ativos:
            stmt = stmt.where(Bico.ativo.is_(True))
        if plataforma_id is not None:
            stmt = stmt.where(Bico.plataforma_id == plataforma_id)
        if produto is not None:
            stmt = stmt.where(Bico.produto == produto)
        elif produto_id is not None:
            stmt = stmt.where(Bico.produto_id == produto_id)

        stmt = stmt.order_by(Bico.identificador_bico.asc(), Bico.id.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def salvar(self, session: AsyncSession, bico: Bico) -> Bico:
        session.add(bico)
        await session.flush()
        await session.refresh(bico)
        return bico

    async def excluir(self, session: AsyncSession, bico: Bico) -> None:
        await session.delete(bico)
        await session.flush()

    async def sincronizar_vinculos_tanques(
        self, session: AsyncSession, bico_id: int, novos_tanque_ids: List[int]
    ) -> None:
        """Sincroniza os vínculos de tanques na tabela bico_tanque_vinculo."""
        # 1. Remover vínculos de tanques que foram desmarcados
        if novos_tanque_ids:
            stmt_del = delete(BicoTanqueVinculo).where(
                BicoTanqueVinculo.bico_id == bico_id,
                BicoTanqueVinculo.tanque_id.not_in(novos_tanque_ids),
            )
        else:
            stmt_del = delete(BicoTanqueVinculo).where(
                BicoTanqueVinculo.bico_id == bico_id
            )
        await session.execute(stmt_del)

        # 2. Obter vínculos que já existem para este bico
        stmt_existentes = select(BicoTanqueVinculo.tanque_id).where(
            BicoTanqueVinculo.bico_id == bico_id
        )
        res = await session.execute(stmt_existentes)
        tanques_ja_vinculados = set(res.scalars().all())

        # 3. Inserir novos vínculos
        for tid in novos_tanque_ids:
            if tid not in tanques_ja_vinculados:
                vinculo = BicoTanqueVinculo(
                    bico_id=bico_id,
                    tanque_id=tid,
                    is_padrao=True,
                    ativo=True,
                )
                session.add(vinculo)
        await session.flush()


bico_repository = BicoRepository()
