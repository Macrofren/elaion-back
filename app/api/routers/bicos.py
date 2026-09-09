"""Roteador da API v1 para Gestão de Bicos de Operação e Conexão do Terminal."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    exige_qualquer_permissao,
    get_db_session,
    resolver_terminal_ativo,
)
from app.domain.models import TipoOperacao, Usuario
from app.domain.schemas import (
    AtualizarTerminalBicosRequestDTO,
    BicoCreateDTO,
    BicoResponseDTO,
    BicoUpdateDTO,
)
from app.services.bicos_service import bicos_service

router = APIRouter(tags=["Gestão de Bicos"])

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
# 1. ENDPOINTS GRANULARES REST SOB /bicos
# =============================================================================

@router.get(
    "/bicos",
    response_model=List[BicoResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Bicos de Conexão do Terminal",
    description=(
        "Retorna os bicos cadastrados no terminal ativo com detalhes da plataforma, "
        "combustível operado e tanques vinculados. "
        "Requer permissão 'sirac:config:terminal:tanques_ver' ou Master."
    ),
)
async def listar_bicos(
    request: Request,
    apenas_ativos: bool = Query(False, description="Filtrar apenas bicos ativos"),
    plataforma_id: Optional[int] = Query(None, description="Filtrar por plataforma"),
    tipo_operacao: Optional[TipoOperacao] = Query(None, description="Filtrar por tipo de operação (CARREGAMENTO ou DESCARGA)"),
    produto: Optional[str] = Query(None, description="Filtrar por enum do combustível"),
    produto_id: Optional[int] = Query(None, description="Filtrar por ID do produto (legado)"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[BicoResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await bicos_service.listar_bicos(
        session,
        terminal_id,
        apenas_ativos=apenas_ativos,
        plataforma_id=plataforma_id,
        tipo_operacao=tipo_operacao,
        produto=produto,
        produto_id=produto_id,
    )


@router.post(
    "/bicos",
    response_model=BicoResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Bico de Conexão no Terminal",
    description=(
        "Cadastra um novo bico vinculado ao terminal ativo, validando plataforma e compatibilidade de combustível dos tanques. "
        "Requer permissão 'sirac:config:terminal:tanques_registrar' ou Master."
    ),
)
async def cadastrar_bico(
    request: Request,
    payload: BicoCreateDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_REGISTRAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> BicoResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await bicos_service.cadastrar_bico(session, terminal_id, payload)


@router.get(
    "/bicos/{bico_id}",
    response_model=BicoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter Detalhes de um Bico",
    description="Retorna os detalhes de um bico específico vinculado ao terminal ativo.",
)
async def obter_bico(
    request: Request,
    bico_id: int,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> BicoResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await bicos_service.obter_bico(session, terminal_id, bico_id)


@router.put(
    "/bicos/{bico_id}",
    response_model=BicoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Atualizar Bico de Conexão",
    description=(
        "Atualiza plataforma, combustível, tanques vinculados ou status ativo do bico. "
        "Requer permissão 'sirac:config:terminal:tanques_editar' ou Master."
    ),
)
async def atualizar_bico(
    request: Request,
    bico_id: int,
    payload: BicoUpdateDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_EDITAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> BicoResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await bicos_service.atualizar_bico(session, terminal_id, bico_id, payload)


@router.delete(
    "/bicos/{bico_id}",
    response_model=BicoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Desativar Bico (Soft Delete)",
    description=(
        "Desativa logicamente o bico (ativo = False) para preservar integridade com histórico operacional. "
        "Requer permissão 'sirac:config:terminal:tanques_editar' ou Master."
    ),
)
async def desativar_bico(
    request: Request,
    bico_id: int,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_EDITAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> BicoResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await bicos_service.desativar_bico(session, terminal_id, bico_id)


@router.patch(
    "/bicos/{bico_id}/toggle-status",
    response_model=BicoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Alternar Status do Bico",
    description="Alterna entre ativo e inativo o status do bico de conexão.",
)
async def alternar_status_bico(
    request: Request,
    bico_id: int,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_EDITAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> BicoResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await bicos_service.alternar_status_bico(session, terminal_id, bico_id)


# =============================================================================
# 2. ENDPOINTS COMPATÍVEIS SOB /terminal/bicos (Lote e Consulta)
# =============================================================================

@router.get(
    "/terminal/bicos",
    response_model=List[BicoResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Bicos do Terminal (Sub-recurso)",
    description="Retorna todos os bicos associados ao terminal ativo.",
)
async def listar_bicos_terminal(
    request: Request,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[BicoResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await bicos_service.listar_bicos(session, terminal_id)


@router.put(
    "/terminal/bicos",
    response_model=List[BicoResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Sincronizar Bicos do Terminal em Lote",
    description=(
        "Endpoint consumido pelo Drawer de Bicos do Terminal para sincronizar múltiplos bicos, "
        "validar tanques/combustíveis e aplicar soft delete nos omitidos."
    ),
)
async def sincronizar_bicos(
    request: Request,
    payload: AtualizarTerminalBicosRequestDTO,
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_SINCRONIZAR)),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[BicoResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await bicos_service.sincronizar_bicos_terminal(session, terminal_id, payload)
