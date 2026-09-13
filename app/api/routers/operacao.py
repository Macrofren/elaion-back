"""
Roteador da API v1 para Controle de Acesso e Operações de Pátio do Terminal.
Implementação completa integrada ao banco de dados via Clean Architecture (operacao_service).
"""

from datetime import date
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
    AtualizarVeiculoDescargaRequestDTO,
    AvancarColetaRequestDTO,
    CancelarAcessoRequestDTO,
    ControleAcessoContagensResponseDTO,
    ControleAcessoItemDTO,
    EntradaVeiculoRequestDTO,
    NovoVeiculoDescargaRequestDTO,
    PaginatedControleAcessoResponseDTO,
    RegistroDescargaRequestDTO,
    RetornarEstadoRequestDTO,
    SaidaVeiculoRequestDTO,
    TransicaoEstadoControleAcessoRequestDTO,
)
from app.services.operacao_service import operacao_service

router = APIRouter(tags=["Controle de Acesso"])

PERMISSOES_VISUALIZAR = [
    "sirac:ca:visualizar_listagem",
    "sirac:ca:visualizar_detalhes",
]
PERMISSOES_ALTERAR_STATUS = [
    "sirac:ca:alterar_status",
]
PERMISSOES_REGISTRAR = [
    "sirac:ca:registrar_veiculo",
    "sirac:ca:editar_veiculo",
    "sirac:ca:alterar_status",
]


def _obter_terminal_id(request: Request, x_terminal_id: Optional[int]) -> int:
    terminal_id = resolver_terminal_ativo(request, x_terminal_id)
    if terminal_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de terminal não informado. Forneça o header 'X-Terminal-ID'.",
        )
    return terminal_id


@router.get(
    "/controle-acesso",
    response_model=PaginatedControleAcessoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar registros de controle de acesso ao terminal",
    description=(
        "Retorna a listagem paginada dos veículos e operações de pátio para o terminal ativo. "
        "Permite busca textual (motorista, placa, NF, transportadora, congênere), filtros por período, "
        "macro-estados da portaria (FILA, ENTRADA, COLETA, SAIDA, CANCELADO) e combustíveis."
    ),
)
async def listar_controle_acesso(
    request: Request,
    data: Optional[date] = Query(
        None,
        description="Data de referência única (filtra apenas esta data)",
    ),
    data_inicio: Optional[str] = Query(
        None,
        description="Data inicial do período (YYYY-MM-DD)",
    ),
    data_fim: Optional[str] = Query(
        None,
        description="Data final do período (YYYY-MM-DD)",
    ),
    busca: Optional[str] = Query(
        None,
        description="Busca textual por motorista, placa, NF, transportadora ou distribuidora congênere",
    ),
    estados: Optional[List[str]] = Query(
        None,
        description="Filtro por macro-estados (ex: FILA, ENTRADA, COLETA, SAIDA, CANCELADO)",
    ),
    estado: Optional[str] = Query(
        None,
        description="Filtro por estado único ou separado por vírgula",
    ),
    operacoes: Optional[List[str]] = Query(
        None,
        description="Filtrar por tipo de operação (DESCARGA, CARREGAMENTO)",
    ),
    operacao: Optional[str] = Query(
        None,
        description="Filtro por tipo de operação único ou separado por vírgula",
    ),
    produtos: Optional[List[str]] = Query(
        None,
        description="Filtrar por produtos/combustíveis transportados",
    ),
    produto: Optional[str] = Query(
        None,
        description="Filtro por produto único ou separado por vírgula",
    ),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Quantidade de registros por página"),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedControleAcessoResponseDTO:
    """Listagem paginada do controle de acesso consultada diretamente do banco de dados."""
    terminal_id = _obter_terminal_id(request, x_terminal_id)

    # Harmonizar parâmetros separados por vírgula
    estados_consolidados: List[str] = []
    if estados:
        for e in estados:
            estados_consolidados.extend([x.strip() for x in e.split(",") if x.strip()])
    if estado:
        estados_consolidados.extend([x.strip() for x in estado.split(",") if x.strip()])

    operacoes_consolidadas: List[str] = []
    if operacoes:
        for op in operacoes:
            operacoes_consolidadas.extend([x.strip() for x in op.split(",") if x.strip()])
    if operacao:
        operacoes_consolidadas.extend([x.strip() for x in operacao.split(",") if x.strip()])

    produtos_consolidados: List[str] = []
    if produtos:
        for p in produtos:
            produtos_consolidados.extend([x.strip() for x in p.split(",") if x.strip()])
    if produto:
        produtos_consolidados.extend([x.strip() for x in produto.split(",") if x.strip()])

    d_inicio = data_inicio
    d_fim = data_fim
    if data and not d_inicio and not d_fim:
        d_inicio = data.isoformat()
        d_fim = data.isoformat()

    return await operacao_service.listar_veiculos(
        session=session,
        terminal_id=terminal_id,
        busca=busca,
        estados=estados_consolidados or None,
        operacoes=operacoes_consolidadas or None,
        produtos=produtos_consolidados or None,
        data_inicio=d_inicio,
        data_fim=d_fim,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/controle-acesso/contagens",
    response_model=ControleAcessoContagensResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter contadores por estado para as abas do controle de acesso",
    description=(
        "Retorna as contagens consolidadas de veículos em cada estado (FILA/AGUARDANDO, ENTRADA, "
        "COLETA, SAIDA, CANCELADO e TOTAL) para alimentação em tempo real dos badges das abas."
    ),
)
async def obter_contagens_controle_acesso(
    request: Request,
    data: Optional[date] = Query(
        None,
        description="Data de referência única para contagem",
    ),
    data_inicio: Optional[str] = Query(
        None,
        description="Data inicial para contagem (YYYY-MM-DD)",
    ),
    data_fim: Optional[str] = Query(
        None,
        description="Data final para contagem (YYYY-MM-DD)",
    ),
    operacao: Optional[str] = Query(
        None,
        description="Filtrar por tipo de operação (DESCARGA ou CARREGAMENTO)",
    ),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoContagensResponseDTO:
    """Contagens dos seletores de abas consultadas diretamente do banco de dados."""
    terminal_id = _obter_terminal_id(request, x_terminal_id)

    d_inicio = data_inicio
    d_fim = data_fim
    if data and not d_inicio and not d_fim:
        d_inicio = data.isoformat()
        d_fim = data.isoformat()

    return await operacao_service.obter_contagens(
        session=session,
        terminal_id=terminal_id,
        data_inicio=d_inicio,
        data_fim=d_fim,
        tipo_operacao_str=operacao,
    )


@router.get(
    "/controle-acesso/{id}",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter detalhes completos do veículo no controle de acesso",
    description="Retorna todas as informações do veículo, compartimentos e histórico auditado para o Drawer de Detalhes.",
)
async def obter_detalhes_veiculo(
    id: int,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await operacao_service.obter_detalhes_veiculo(
        session=session, operacao_id=id, terminal_id=terminal_id
    )


@router.post(
    "/controle-acesso",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo veículo na portaria (Fila)",
    description=(
        "Registra a chegada de um caminhão-tanque na portaria do terminal com estado inicial FILA. "
        "Suporta payload em formato plano ou agrupado por produto (enviado pelo frontend)."
    ),
)
async def registrar_veiculo(
    payload: NovoVeiculoDescargaRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_REGISTRAR)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await operacao_service.cadastrar_veiculo_descarga(
        session=session,
        terminal_id=terminal_id,
        usuario_id=_usuario.id,
        dto=payload,
    )


@router.put(
    "/controle-acesso/{id}",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_200_OK,
    summary="Atualizar dados cadastrais do veículo na fila",
    description="Permite a edição dos dados cadastrais exclusivamente enquanto o veículo estiver no estado FILA.",
)
async def atualizar_veiculo(
    id: int,
    payload: AtualizarVeiculoDescargaRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_REGISTRAR)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await operacao_service.atualizar_veiculo_fila(
        session=session,
        operacao_id=id,
        terminal_id=terminal_id,
        usuario_id=_usuario.id,
        dto=payload,
    )


@router.patch(
    "/controle-acesso/{id}/estado",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_200_OK,
    summary="Transitar estado do veículo na portaria",
    description="Executa a transição de estado validada pela máquina de estados (ex: FILA -> ENTRADA -> SAIDA).",
)
async def transitar_estado_veiculo(
    id: int,
    payload: TransicaoEstadoControleAcessoRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_ALTERAR_STATUS)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await operacao_service.transitar_estado(
        session=session,
        operacao_id=id,
        terminal_id=terminal_id,
        usuario=_usuario,
        novo_estado=payload.estado,
        motivo=payload.motivo or payload.observacao,
        bafometro_resultado=payload.bafometro_resultado,
        bafometro_valor=payload.bafometro_valor,
    )


@router.patch(
    "/controle-acesso/{id}/entrada",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_200_OK,
    summary="Registrar entrada com teste de bafômetro",
    description="Valida o teste de bafômetro e transiciona o veículo de FILA para ENTRADA.",
)
async def registrar_entrada(
    id: int,
    payload: EntradaVeiculoRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_ALTERAR_STATUS)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    from app.domain.models import EstadoVeiculo

    return await operacao_service.transitar_estado(
        session=session,
        operacao_id=id,
        terminal_id=terminal_id,
        usuario=_usuario,
        novo_estado=EstadoVeiculo.ENTRADA,
        motivo=payload.observacao,
        bafometro_resultado=payload.bafometro_resultado,
        bafometro_valor=payload.bafometro_valor,
    )


@router.patch(
    "/controle-acesso/{id}/avancar-coleta",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_200_OK,
    summary="Avançar veículo para etapa de amostragem/coleta no pátio",
    description="Permitido exclusivamente a partir de ENTRADA.",
)
async def avancar_para_coleta(
    id: int,
    payload: AvancarColetaRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_ALTERAR_STATUS)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    from app.domain.models import EstadoVeiculo

    return await operacao_service.transitar_estado(
        session=session,
        operacao_id=id,
        terminal_id=terminal_id,
        usuario=_usuario,
        novo_estado=EstadoVeiculo.COLETA,
        motivo=payload.observacao,
    )


@router.patch(
    "/controle-acesso/{id}/saida",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_200_OK,
    summary="Registrar saída do veículo após término da operação",
    description="Finaliza a operação e registra a liberação na portaria (preenchendo data/hora de saída).",
)
async def registrar_saida(
    id: int,
    payload: SaidaVeiculoRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_ALTERAR_STATUS)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    from app.domain.models import EstadoVeiculo

    return await operacao_service.transitar_estado(
        session=session,
        operacao_id=id,
        terminal_id=terminal_id,
        usuario=_usuario,
        novo_estado=EstadoVeiculo.SAIDA,
        motivo=payload.observacao,
    )


@router.patch(
    "/controle-acesso/{id}/retornar-estado",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_200_OK,
    summary="Retornar veículo para o estado anterior com justificativa obrigatória",
    description="Permite reversão justificada: de COLETA para ENTRADA, ou de ENTRADA para FILA.",
)
async def retornar_estado_veiculo(
    id: int,
    payload: RetornarEstadoRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_ALTERAR_STATUS)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await operacao_service.retornar_estado_anterior(
        session=session,
        operacao_id=id,
        terminal_id=terminal_id,
        usuario=_usuario,
        motivo=payload.motivo,
    )


@router.patch(
    "/controle-acesso/{id}/cancelar",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_200_OK,
    summary="Cancelar acesso do veículo na portaria",
    description="Cancela a operação do veículo enquanto este estiver na FILA ou na ENTRADA.",
)
async def cancelar_acesso_veiculo(
    id: int,
    payload: CancelarAcessoRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_ALTERAR_STATUS)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await operacao_service.cancelar_acesso(
        session=session,
        operacao_id=id,
        terminal_id=terminal_id,
        usuario=_usuario,
        motivo=payload.motivo,
    )


@router.post(
    "/controle-acesso/descarga",
    response_model=ControleAcessoItemDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo veículo de descarga (Alias legado)",
    description="Endpoint mantido por compatibilidade; direciona para a criação de veículo na fila.",
)
async def registrar_veiculo_descarga(
    payload: RegistroDescargaRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_REGISTRAR)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoItemDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await operacao_service.cadastrar_veiculo_descarga(
        session=session,
        terminal_id=terminal_id,
        usuario_id=_usuario.id,
        dto=payload,
    )