"""Repositório assíncrono para persistência e consulta de Amostras de Triagem/Laboratório."""

from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Amostra, OperacaoCompartimento, OperacaoVeiculo


def _amostra_options():
    """Carregamento ansioso das relações necessárias para DTOs de Amostra."""
    return [
        selectinload(Amostra.operacao),
        selectinload(Amostra.compartimento),
        selectinload(Amostra.produto),
        selectinload(Amostra.operador),
        selectinload(Amostra.analise),
    ]


class AmostraRepository:
    """Operações de banco de dados para a entidade Amostra."""

    async def get_by_id(
        self, session: AsyncSession, amostra_id: int
    ) -> Optional[Amostra]:
        """Busca uma amostra pelo ID com os relacionamentos pré-carregados."""
        raise NotImplementedError("Método a ser implementado.")

    async def get_by_codigo(
        self, session: AsyncSession, codigo_amostra: str
    ) -> Optional[Amostra]:
        """Busca uma amostra pelo código único."""
        raise NotImplementedError("Método a ser implementado.")

    async def listar_por_operacao(
        self, session: AsyncSession, operacao_id: int
    ) -> List[Amostra]:
        """Lista todas as amostras colhidas para uma operação de veículo."""
        raise NotImplementedError("Método a ser implementado.")

    async def criar(
        self, session: AsyncSession, amostra: Amostra
    ) -> Amostra:
        """Persiste uma nova instância da entidade Amostra."""
        raise NotImplementedError("Método a ser implementado.")

    async def criar_lote(
        self, session: AsyncSession, amostras: List[Amostra]
    ) -> List[Amostra]:
        """Persiste um lote de instâncias de Amostra."""
        raise NotImplementedError("Método a ser implementado.")

    async def obter_proximo_codigo_amostra(
        self, session: AsyncSession, operacao_id: int
    ) -> str:
        """Calcula ou gera o identificador único de código de amostra."""
        raise NotImplementedError("Método a ser implementado.")


amostra_repository = AmostraRepository()
