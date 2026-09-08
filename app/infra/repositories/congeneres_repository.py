"""Repositório de acesso a dados de Congênere."""

from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Congenere


class CongenereRepository:
    """Operações de banco de dados para a entidade Congenere vinculada ao terminal."""

    async def get_by_id(self, session: AsyncSession, congenere_id: int) -> Optional[Congenere]:
        stmt = select(Congenere).where(Congenere.id == congenere_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_cnpj_terminal(
        self, session: AsyncSession, terminal_id: int, cnpj: str
    ) -> Optional[Congenere]:
        stmt = select(Congenere).where(
            Congenere.terminal_id == terminal_id,
            Congenere.cnpj == cnpj,
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_por_terminal(
        self, session: AsyncSession, terminal_id: int, busca: Optional[str] = None
    ) -> List[Congenere]:
        stmt = select(Congenere).where(Congenere.terminal_id == terminal_id)

        if busca:
            clean_digits = "".join(filter(str.isdigit, busca))
            conditions = [
                Congenere.razao_social.ilike(f"%{busca}%"),
                Congenere.email.ilike(f"%{busca}%"),
                Congenere.cnpj.ilike(f"%{busca}%"),
            ]
            if clean_digits:
                conditions.append(Congenere.cnpj.ilike(f"%{clean_digits}%"))
                conditions.append(Congenere.telefone.ilike(f"%{clean_digits}%"))
            if Congenere.inscricao_estadual is not None:
                conditions.append(Congenere.inscricao_estadual.ilike(f"%{busca}%"))
            if Congenere.cidade is not None:
                conditions.append(Congenere.cidade.ilike(f"%{busca}%"))
            if Congenere.uf is not None:
                conditions.append(Congenere.uf.ilike(f"%{busca}%"))

            stmt = stmt.where(or_(*conditions))

        stmt = stmt.order_by(Congenere.razao_social.asc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def criar(self, session: AsyncSession, terminal_id: int, dados: dict) -> Congenere:
        congenere = Congenere(terminal_id=terminal_id, **dados)
        session.add(congenere)
        await session.flush()
        await session.refresh(congenere)
        return congenere

    async def atualizar(
        self, session: AsyncSession, congenere: Congenere, dados: dict
    ) -> Congenere:
        for campo, valor in dados.items():
            if hasattr(congenere, campo) and valor is not None:
                setattr(congenere, campo, valor)
        await session.flush()
        await session.refresh(congenere)
        return congenere


congenere_repository = CongenereRepository()
