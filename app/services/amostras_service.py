"""Serviço de Negócio para Gestão e Registro de Amostras (Triagem / Laboratório)."""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    ConflitoException,
    ItemNaoEncontradoException,
    RegraNegocioException,
)
from app.domain.schemas import (
    RegistrarAmostrasRequestDTO,
    RegistrarAmostrasResponseDTO,
)
from app.infra.repositories.amostra_repository import amostra_repository
from app.infra.repositories.operacao_repository import operacao_repository


class AmostrasService:
    """Regras de negócio e casos de uso de Amostragem."""

    async def registrar_amostras(
        self,
        session: AsyncSession,
        payload: RegistrarAmostrasRequestDTO,
        usuario_id: int,
        terminal_id: Optional[int] = None,
    ) -> RegistrarAmostrasResponseDTO:
        """
        Caso de uso: Registrar novas amostras de um veículo a partir do formulário do drawer.

        Args:
            session: Sessão assíncrona do SQLAlchemy.
            payload: Dados validados da requisição (contrato DTO a ser preenchido).
            usuario_id: ID do operador autenticado.
            terminal_id: ID do terminal ativo.

        Returns:
            RegistrarAmostrasResponseDTO: Resposta com dados da persistência.
        """
        raise NotImplementedError("Método a ser implementado pelo desenvolvedor.")


amostras_service = AmostrasService()
