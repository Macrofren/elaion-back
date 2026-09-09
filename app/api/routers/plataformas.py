"""Roteador da API v1 para Gestão de Plataformas de Operação do Terminal."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    exige_qualquer_permissao,
    get_db_session,
    resolver_terminal_ativo,
)
from app.domain.models import TipoPlataforma, Usuario
from app.domain.schemas import (
    AtualizarTerminalPlataformasRequestDTO,
    PlataformaCreateDTO,
    PlataformaResponseDTO,
    PlataformaUpdateDTO,
)
from app.services.plataformas_service import plataformas_service

router = APIRouter(tags=["Gestão de Plataformas"])

# Permissões RBAC para operações com plataformas
PERMISSOES_VISUALIZAR = [
    "sirac:config:terminal:tanques_ver",
    "sirac:config:terminal:dados_cadastrais",
]
PERMISSOES_REGISTRAR = [
    "sirac:config:terminal:tanques_registrar",
    "sirac:config:terminal:dados_editar",
]
PERMISSOES_EDITAR = [
    "sirac:config:terminal:tanques_editar",
    "sirac:config:terminal:dados_editar",
]
PERMISSOES_SINCRONIZAR = [
    "sirac:config:terminal:tanques_editar",
    "sirac:config:terminal:tanques_registrar",
    "sirac:config:terminal:dados_editar",
]


def _obter_terminal_id(request: Request, x_terminal_id: Optional[int]) -> int:
    terminal_id = resolver_terminal_ativo(request, x_terminal_id)
    if terminal_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de terminal não informado. Forneça o header 'X-Terminal-ID'.",
        )
    return terminal_id


# =============================================================================
# 1. ENDPOINTS GRANULARES REST SOB /plataformas
# =============================================================================

@router.get(
    "/plataformas",
    response_model=List[PlataformaResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Plataformas de Operação do Terminal",
    description=(
        "Retorna as plataformas cadastradas no terminal ativo. "
        "Permite filtrar por status ativo e tipo operacional. "
        "Requer permissão 'sirac:config:terminal:tanques_ver' ou Master."
    ),
)
async def listar_plataformas(
    request: Request,
    apenas_ativos: bool = Query(False, description="Filtrar apenas plataformas ativas"),
    tipo: Optional[TipoPlataforma] = Query(None, description="Filtrar por tipo de plataforma"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[PlataformaResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await plataformas_service.listar_plataformas(
        session, terminal_id, apenas_ativos=apenas_ativos, tipo=tipo
    )


@router.post(
    "/plataformas",
    response_model=PlataformaResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Plataforma de Operação no Terminal",
    description=(
        "Cadastra uma nova plataforma de operação vinculada ao terminal ativo. "
        "Requer permissão 'sirac:config:terminal:tanques_registrar' ou Master."
    ),
)
async def cadastrar_plataforma(
    request: Request,
    payload: PlataformaCreateDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_REGISTRAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> PlataformaResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await plataformas_service.cadastrar_plataforma(session, terminal_id, payload)


@router.get(
    "/plataformas/{plataforma_id}",
    response_model=PlataformaResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter Detalhes de uma Plataforma",
    description="Retorna os detalhes de uma plataforma específica vinculada ao terminal ativo.",
)
async def obter_plataforma(
    request: Request,
    plataforma_id: int,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> PlataformaResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await plataformas_service.obter_plataforma(session, terminal_id, plataforma_id)


@router.put(
    "/plataformas/{plataforma_id}",
    response_model=PlataformaResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Atualizar Plataforma de Operação",
    description=(
        "Atualiza identificador, nome, tipo ou status ativo da plataforma. "
        "Requer permissão 'sirac:config:terminal:tanques_editar' ou Master."
    ),
)
async def atualizar_plataforma(
    request: Request,
    plataforma_id: int,
    payload: PlataformaUpdateDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_EDITAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> PlataformaResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await plataformas_service.atualizar_plataforma(
        session, terminal_id, plataforma_id, payload
    )


@router.delete(
    "/plataformas/{plataforma_id}",
    response_model=PlataformaResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Desativar Plataforma (Soft Delete)",
    description=(
        "Desativa logicamente a plataforma (ativo = False) para preservar a integridade "
        "referencial com bicos e histórico operacional. "
        "Requer permissão 'sirac:config:terminal:tanques_editar' ou Master."
    ),
)
async def desativar_plataforma(
    request: Request,
    plataforma_id: int,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_EDITAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> PlataformaResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await plataformas_service.desativar_plataforma(session, terminal_id, plataforma_id)


@router.patch(
    "/plataformas/{plataforma_id}/toggle-status",
    response_model=PlataformaResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Alternar Status da Plataforma",
    description="Alterna entre ativo e inativo o status da plataforma de operação.",
)
async def alternar_status_plataforma(
    request: Request,
    plataforma_id: int,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_EDITAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> PlataformaResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await plataformas_service.alternar_status_plataforma(
        session, terminal_id, plataforma_id
    )


# =============================================================================
# 2. ENDPOINTS COMPATÍVEIS SOB /terminal/plataformas (Lote e Consulta)
# =============================================================================

@router.get(
    "/terminal/plataformas",
    response_model=List[PlataformaResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Plataformas do Terminal (Sub-recurso)",
    description="Retorna todas as plataformas associadas ao terminal ativo.",
)
async def listar_plataformas_terminal(
    request: Request,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[PlataformaResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await plataformas_service.listar_plataformas(session, terminal_id)


@router.put(
    "/terminal/plataformas",
    response_model=List[PlataformaResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Sincronizar Plataformas do Terminal em Lote",
    description=(
        "Endpoint consumido pelo Drawer de configurações do Terminal para sincronizar "
        "múltiplas plataformas, adicionar novas e desativar (soft delete) as removidas em uma operação atômica."
    ),
)
async def sincronizar_plataformas(
    request: Request,
    payload: AtualizarTerminalPlataformasRequestDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_SINCRONIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[PlataformaResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await plataformas_service.sincronizar_plataformas_terminal(
        session, terminal_id, payload
    )
