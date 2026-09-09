"""Roteador da API v1 para Gestão de Tanques de Armazenamento do Terminal."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    exige_qualquer_permissao,
    get_db_session,
    resolver_terminal_ativo,
)
from app.domain.models import Usuario
from app.domain.schemas import (
    AtualizarTerminalTanquesRequestDTO,
    TanqueCreateDTO,
    TanqueResponseDTO,
    TanqueUpdateDTO,
)
from app.services.tanques_service import tanques_service

router = APIRouter(tags=["Gestão de Tanques"])

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
# 1. ENDPOINTS GRANULARES REST SOB /tanques
# =============================================================================

@router.get(
    "/tanques",
    response_model=List[TanqueResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Tanques de Armazenamento do Terminal",
    description=(
        "Retorna todos os tanques cadastrados no terminal ativo. "
        "Permite filtrar por status ativo e produto/combustível específico. "
        "Requer permissão 'sirac:config:terminal:tanques_ver' ou Master."
    ),
)
async def listar_tanques(
    request: Request,
    apenas_ativos: bool = Query(False, description="Filtrar apenas tanques ativos"),
    produto: Optional[str] = Query(None, description="Filtrar por enum do combustível"),
    produto_id: Optional[int] = Query(None, description="Filtrar por ID do combustível (legado)"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[TanqueResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await tanques_service.listar_tanques(
        session,
        terminal_id,
        apenas_ativos=apenas_ativos,
        produto=produto,
        produto_id=produto_id,
    )


@router.post(
    "/tanques",
    response_model=TanqueResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Tanque de Armazenamento no Terminal",
    description=(
        "Cadastra um novo tanque de armazenamento vinculado ao terminal ativo. "
        "Requer permissão 'sirac:config:terminal:tanques_registrar' ou Master."
    ),
)
async def cadastrar_tanque(
    request: Request,
    payload: TanqueCreateDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_REGISTRAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> TanqueResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await tanques_service.cadastrar_tanque(session, terminal_id, payload)


@router.get(
    "/tanques/{tanque_id}",
    response_model=TanqueResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter Detalhes de um Tanque de Armazenamento",
    description="Retorna os dados completos de um tanque específico do terminal ativo.",
)
async def obter_tanque(
    request: Request,
    tanque_id: int,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> TanqueResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await tanques_service.obter_tanque(session, terminal_id, tanque_id)


@router.put(
    "/tanques/{tanque_id}",
    response_model=TanqueResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Atualizar Tanque de Armazenamento",
    description=(
        "Atualiza capacidades, produto vinculado, identificador ou status do tanque. "
        "Requer permissão 'sirac:config:terminal:tanques_editar' ou Master."
    ),
)
async def atualizar_tanque(
    request: Request,
    tanque_id: int,
    payload: TanqueUpdateDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_EDITAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> TanqueResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await tanques_service.atualizar_tanque(session, terminal_id, tanque_id, payload)


@router.patch(
    "/tanques/{tanque_id}/toggle-status",
    response_model=TanqueResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Alternar Status do Tanque",
    description="Alterna entre ativo e inativo o status do tanque de armazenamento.",
)
async def alternar_status_tanque(
    request: Request,
    tanque_id: int,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_EDITAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> TanqueResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await tanques_service.alternar_status_tanque(session, terminal_id, tanque_id)


# =============================================================================
# 2. ENDPOINTS COMPATÍVEIS SOB /terminal/tanques (Lote e Consulta)
# =============================================================================

@router.get(
    "/terminal/tanques",
    response_model=List[TanqueResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Tanques do Terminal (Sub-recurso)",
    description="Retorna todos os tanques associados ao terminal ativo.",
)
async def listar_tanques_terminal(
    request: Request,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[TanqueResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await tanques_service.listar_tanques(session, terminal_id)


@router.put(
    "/terminal/tanques",
    response_model=List[TanqueResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Sincronizar Tanques do Terminal em Lote",
    description=(
        "Endpoint consumido pelo Drawer de Tanques do Terminal para sincronizar múltiplos tanques, "
        "adicionar novos, atualizar existentes e aplicar soft-delete nos removidos."
    ),
)
async def sincronizar_tanques(
    request: Request,
    payload: AtualizarTerminalTanquesRequestDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_SINCRONIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[TanqueResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await tanques_service.sincronizar_tanques_terminal(session, terminal_id, payload)
