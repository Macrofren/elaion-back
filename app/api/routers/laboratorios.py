"""Roteador da API v1 para Gestão de Laboratórios do Terminal."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import exige_permissao, get_db_session, resolver_terminal_ativo
from app.domain.models import Usuario
from app.domain.schemas import (
    AtualizarTerminalLaboratoriosRequestDTO,
    LaboratorioCreateDTO,
    LaboratorioResponseDTO,
    LaboratorioUpdateDTO,
)
from app.services.laboratorios_service import laboratorios_service

router = APIRouter(tags=["Gestão de Laboratórios"])


def _obter_terminal_id(request: Request, x_terminal_id: Optional[int]) -> int:
    terminal_id = resolver_terminal_ativo(request, x_terminal_id)
    if terminal_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de terminal não informado. Forneça o header 'X-Terminal-ID'.",
        )
    return terminal_id


# =============================================================================
# 1. ENDPOINTS GRANULARES REST SOB /laboratorios
# =============================================================================

@router.get(
    "/laboratorios",
    response_model=List[LaboratorioResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Laboratórios do Terminal",
    description=(
        "Retorna todos os laboratórios cadastrados no terminal ativo. "
        "Requer permissão 'sirac:config:terminal:dados_cadastrais' ou usuário Master."
    ),
)
async def listar_laboratorios(
    request: Request,
    apenas_ativos: bool = Query(False, description="Filtrar apenas laboratórios ativos"),
    _usuario: Usuario = Depends(exige_permissao("sirac:config:terminal:dados_cadastrais")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[LaboratorioResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await laboratorios_service.listar_laboratorios(
        session, terminal_id, apenas_ativos=apenas_ativos
    )


@router.post(
    "/laboratorios",
    response_model=LaboratorioResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Laboratório no Terminal",
    description=(
        "Cadastra um novo laboratório (próprio ou terceirizado) vinculado ao terminal ativo. "
        "Requer permissão 'sirac:config:terminal:dados_editar' ou usuário Master."
    ),
)
async def cadastrar_laboratorio(
    request: Request,
    payload: LaboratorioCreateDTO,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:terminal:dados_editar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> LaboratorioResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await laboratorios_service.cadastrar_laboratorio(session, terminal_id, payload)


@router.get(
    "/laboratorios/{laboratorio_id}",
    response_model=LaboratorioResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter Detalhes de um Laboratório",
)
async def obter_laboratorio(
    request: Request,
    laboratorio_id: int,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:terminal:dados_cadastrais")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> LaboratorioResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await laboratorios_service.obter_laboratorio(session, terminal_id, laboratorio_id)


@router.put(
    "/laboratorios/{laboratorio_id}",
    response_model=LaboratorioResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Atualizar Laboratório",
    description="Atualiza nome, código, is_proprio ou status ativo do laboratório.",
)
async def atualizar_laboratorio(
    request: Request,
    laboratorio_id: int,
    payload: LaboratorioUpdateDTO,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:terminal:dados_editar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> LaboratorioResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await laboratorios_service.atualizar_laboratorio(
        session, terminal_id, laboratorio_id, payload
    )


@router.delete(
    "/laboratorios/{laboratorio_id}",
    response_model=LaboratorioResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Desativar Laboratório (Soft Delete)",
    description=(
        "Desativa logicamente o laboratório (ativo = False) para preservar histórico "
        "de laudos e amostras vinculadas."
    ),
)
async def desativar_laboratorio(
    request: Request,
    laboratorio_id: int,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:terminal:dados_editar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> LaboratorioResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await laboratorios_service.desativar_laboratorio(session, terminal_id, laboratorio_id)


@router.patch(
    "/laboratorios/{laboratorio_id}/toggle-status",
    response_model=LaboratorioResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Alternar Status do Laboratório",
)
async def alternar_status_laboratorio(
    request: Request,
    laboratorio_id: int,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:terminal:dados_editar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> LaboratorioResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await laboratorios_service.alternar_status_laboratorio(
        session, terminal_id, laboratorio_id
    )


# =============================================================================
# 2. ENDPOINTS COMPATÍVEIS SOB /terminal/laboratorios (Lote e Consulta)
# =============================================================================

@router.get(
    "/terminal/laboratorios",
    response_model=List[LaboratorioResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Laboratórios do Terminal (Sub-recurso)",
)
async def listar_laboratorios_terminal(
    request: Request,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:terminal:dados_cadastrais")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[LaboratorioResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await laboratorios_service.listar_laboratorios(session, terminal_id)


@router.put(
    "/terminal/laboratorios",
    response_model=List[LaboratorioResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Sincronizar Laboratórios do Terminal em Lote",
    description=(
        "Endpoint consumido pelo Drawer de configurações do Terminal para atualizar múltiplos "
        "laboratórios, adicionar novos e desativar os removidos em uma única operação atômica."
    ),
)
async def sincronizar_laboratorios(
    request: Request,
    payload: AtualizarTerminalLaboratoriosRequestDTO,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:terminal:dados_editar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[LaboratorioResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await laboratorios_service.sincronizar_laboratorios_terminal(
        session, terminal_id, payload
    )
