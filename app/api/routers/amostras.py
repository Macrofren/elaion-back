"""Roteador da API v1 para Gestão e Registro de Amostras (Triagem / Laboratório)."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    exige_qualquer_permissao,
    get_db_session,
    obter_usuario_autenticado,
    resolver_terminal_ativo,
)
from app.domain.models import Usuario
from app.domain.schemas import (
    RegistrarAmostrasRequestDTO,
    RegistrarAmostrasResponseDTO,
)
from app.services.amostras_service import amostras_service

router = APIRouter(tags=["Triagem / Amostras"])

PERMISSOES_REGISTRAR = [
    "sirac:triagem:registrar_amostras",
]


def _obter_terminal_id(request: Request, x_terminal_id: Optional[int]) -> int:
    """Extrai e valida o terminal ID a partir de cabeçalho ou contexto da requisição."""
    terminal_id = resolver_terminal_ativo(request, x_terminal_id)
    if terminal_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de terminal não informado. Forneça o header 'X-Terminal-ID'.",
        )
    return terminal_id


@router.post(
    "/amostras",
    response_model=RegistrarAmostrasResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novas amostras do veículo",
    description=(
        "Registra novas amostras coletadas para os compartimentos de um veículo a partir "
        "do drawer de Nova Amostra na triagem. "
        "Requer permissão 'sirac:triagem:registrar_amostras' ou Master."
    ),
)
async def registrar_amostras(
    request: Request,
    payload: RegistrarAmostrasRequestDTO,
    session: AsyncSession = Depends(get_db_session),
    current_user: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_REGISTRAR)),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> RegistrarAmostrasResponseDTO:
    """
    Endpoint HTTP para submissão do formulário de registro de amostras do veículo.

    Assinatura pronta para orquestrar a chamada ao AmostrasService.
    """
    raise NotImplementedError("Endpoint a ser implementado pelo desenvolvedor.")
