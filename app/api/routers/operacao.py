"""
Roteador da API v1 para Controle de Acesso e Operações de Pátio do Terminal.
Contrato de API definido para visualização no FastAPI Docs (Swagger UI/ReDoc).
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    exige_qualquer_permissao,
    get_db_session,
    resolver_terminal_ativo,
)
from app.domain.models import (
    EstadoVeiculo,
    StatusOperacao,
    TipoCombustivel,
    TipoOperacao,
    Usuario,
)
from app.domain.schemas import (
    ControleAcessoContagensResponseDTO,
    ControleAcessoItemDTO,
    ControleAcessoResponseDTO,
    PaginatedControleAcessoResponseDTO,
    TransicaoEstadoControleAcessoRequestDTO,
)

router = APIRouter(tags=["Controle de Acesso"])

PERMISSOES_VISUALIZAR = [
    "sirac:ca:visualizar_listagem",
]
PERMISSOES_ALTERAR_STATUS = [
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


# Mock / Contrato de amostra para exibição no Swagger docs antes da implementação do banco
_SAMPLE_ITEMS = [
    ControleAcessoItemDTO(
        id=1,
        terminal_id=1,
        estado=EstadoVeiculo.AGUARDANDO,
        status_operacao=StatusOperacao.AGUARDANDO_PORTARIA,
        tipo_operacao=TipoOperacao.CARREGAMENTO,
        data_hora=datetime(2026, 9, 10, 8, 30, tzinfo=timezone.utc),
        motorista="Juliana Ferreira",
        placa="PQR2345",
        numero_nf="000128",
        congenere="Larco",
        congenere_id=2,
        transportadora="Transportadora Rodobrás",
        is_propria=False,
        produtos=[TipoCombustivel.DIESEL_S10_A, TipoCombustivel.ETANOL_HIDRATADO],
        volume_nf=Decimal("9800.00"),
    ),
    ControleAcessoItemDTO(
        id=2,
        terminal_id=1,
        estado=EstadoVeiculo.AGUARDANDO,
        status_operacao=StatusOperacao.AGUARDANDO_PORTARIA,
        tipo_operacao=TipoOperacao.DESCARGA,
        data_hora=datetime(2026, 9, 10, 9, 15, tzinfo=timezone.utc),
        motorista="Roberto Carlos Mendes",
        placa="STU7890",
        numero_nf="000131",
        congenere="Vibra Energia",
        congenere_id=1,
        transportadora="Própria",
        is_propria=True,
        produtos=[TipoCombustivel.GASOLINA_A],
        volume_nf=Decimal("15200.00"),
    ),
    ControleAcessoItemDTO(
        id=3,
        terminal_id=1,
        estado=EstadoVeiculo.ENTRADA,
        status_operacao=StatusOperacao.EM_OPERACAO,
        tipo_operacao=TipoOperacao.CARREGAMENTO,
        data_hora=datetime(2026, 9, 10, 7, 45, tzinfo=timezone.utc),
        motorista="Marcos Antônio Lima",
        placa="VWX3456",
        numero_nf="000133",
        congenere="Raízen",
        congenere_id=3,
        transportadora="Expresso Nordeste",
        is_propria=False,
        produtos=[TipoCombustivel.DIESEL_S500_A],
        volume_nf=Decimal("22500.00"),
    ),
    ControleAcessoItemDTO(
        id=4,
        terminal_id=1,
        estado=EstadoVeiculo.COLETA,
        status_operacao=StatusOperacao.EM_AMOSTRAGEM,
        tipo_operacao=TipoOperacao.DESCARGA,
        data_hora=datetime(2026, 9, 10, 8, 10, tzinfo=timezone.utc),
        motorista="Paulo Henrique Souza",
        placa="YZA6789",
        numero_nf="000136",
        congenere="Ipiranga",
        congenere_id=4,
        transportadora="TransLog Brasil",
        is_propria=False,
        produtos=[TipoCombustivel.ETANOL_ANIDRO, TipoCombustivel.GASOLINA_A],
        volume_nf=Decimal("12000.00"),
    ),
    ControleAcessoItemDTO(
        id=5,
        terminal_id=1,
        estado=EstadoVeiculo.SAIDA,
        status_operacao=StatusOperacao.CONCLUIDO,
        tipo_operacao=TipoOperacao.CARREGAMENTO,
        data_hora=datetime(2026, 9, 10, 6, 30, tzinfo=timezone.utc),
        motorista="Carlos Eduardo Rocha",
        placa="BCD1234",
        numero_nf="000122",
        congenere="Larco",
        congenere_id=2,
        transportadora="Rodoviário Cargas",
        is_propria=False,
        produtos=[TipoCombustivel.DIESEL_S10_A],
        volume_nf=Decimal("30000.00"),
    ),
]


@router.get(
    "/controle-acesso",
    response_model=PaginatedControleAcessoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Listar registros de controle de acesso ao terminal",
    description=(
        "Retorna a listagem paginada dos veículos e operações de pátio para o terminal ativo. "
        "Permite busca textual, filtros por macro-estado, tipo de operação e combustíveis. "
        "Por padrão, filtra as operações da data atual (hoje)."
    ),
)
async def listar_controle_acesso(
    request: Request,
    data: date = Query(
        default_factory=date.today,
        description="Data de referência para a listagem (default: data atual de hoje)",
    ),
    busca: Optional[str] = Query(
        None,
        description="Busca textual por motorista, placa, transportadora ou congênere",
    ),
    estados: Optional[List[EstadoVeiculo]] = Query(
        None,
        description="Filtrar por macro-estados da portaria (ex: AGUARDANDO, ENTRADA, COLETA, SAIDA, CANCELADO)",
    ),
    operacoes: Optional[List[TipoOperacao]] = Query(
        None,
        description="Filtrar por tipo de operação (CARREGAMENTO, DESCARGA)",
    ),
    produtos: Optional[List[TipoCombustivel]] = Query(
        None,
        description="Filtrar por produtos/combustíveis transportados",
    ),
    page: int = Query(1, ge=1, description="Número da página (inicia em 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Quantidade de registros por página"),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedControleAcessoResponseDTO:
    """Contrato de API para listagem paginada do controle de acesso."""
    terminal_id = _obter_terminal_id(request, x_terminal_id)

    # Filtragem em memória sobre o mock até que o repositório/service seja implementado
    itens_filtrados = [item for item in _SAMPLE_ITEMS if item.terminal_id == terminal_id]

    if busca:
        termo = busca.strip().lower()
        itens_filtrados = [
            item
            for item in itens_filtrados
            if termo in item.motorista.lower()
            or termo in item.placa.lower()
            or termo in item.transportadora.lower()
            or termo in item.congenere.lower()
            or termo in item.numero_nf.lower()
        ]

    if estados:
        itens_filtrados = [item for item in itens_filtrados if item.estado in estados]

    if operacoes:
        itens_filtrados = [item for item in itens_filtrados if item.tipo_operacao in operacoes]

    if produtos:
        itens_filtrados = [
            item
            for item in itens_filtrados
            if any(p in produtos for p in item.produtos)
        ]

    total = len(itens_filtrados)
    total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1
    start_idx = (page - 1) * page_size
    itens_paginados = itens_filtrados[start_idx : start_idx + page_size]

    return PaginatedControleAcessoResponseDTO(
        items=itens_paginados,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/controle-acesso/contagens",
    response_model=ControleAcessoContagensResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter contadores por estado para as abas do controle de acesso",
    description=(
        "Retorna as contagens consolidadas de veículos em cada estado (Agendados, Entraram, "
        "Coleta, Saíram, Cancelados e Total) para exibição nos badges das abas."
    ),
)
async def obter_contagens_controle_acesso(
    request: Request,
    data: date = Query(
        default_factory=date.today,
        description="Data de referência para contagem (default: data atual de hoje)",
    ),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_VISUALIZAR)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoContagensResponseDTO:
    """Contrato de API para contagens dos seletores de abas."""
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    itens = [item for item in _SAMPLE_ITEMS if item.terminal_id == terminal_id]

    contagens = {
        EstadoVeiculo.AGUARDANDO: 0,
        EstadoVeiculo.ENTRADA: 0,
        EstadoVeiculo.COLETA: 0,
        EstadoVeiculo.SAIDA: 0,
        EstadoVeiculo.CANCELADO: 0,
    }
    for item in itens:
        if item.estado in contagens:
            contagens[item.estado] += 1

    return ControleAcessoContagensResponseDTO(
        AGUARDANDO=contagens[EstadoVeiculo.AGUARDANDO],
        ENTRADA=contagens[EstadoVeiculo.ENTRADA],
        COLETA=contagens[EstadoVeiculo.COLETA],
        SAIDA=contagens[EstadoVeiculo.SAIDA],
        CANCELADO=contagens[EstadoVeiculo.CANCELADO],
        total=len(itens),
    )


@router.patch(
    "/controle-acesso/{id}/estado",
    response_model=ControleAcessoResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Transitar estado do veículo na portaria (Ação rápida)",
    description=(
        "Permite que o operador de portaria realize a transição rápida de estado "
        "(ex: de AGUARDANDO para ENTRADA, ou de ENTRADA para SAIDA)."
    ),
)
async def transitar_estado_veiculo(
    id: int,
    payload: TransicaoEstadoControleAcessoRequestDTO,
    request: Request,
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
    _usuario: Usuario = Depends(exige_qualquer_permissao(PERMISSOES_ALTERAR_STATUS)),
    session: AsyncSession = Depends(get_db_session),
) -> ControleAcessoResponseDTO:
    """Contrato de API para transição rápida de estado na portaria."""
    terminal_id = _obter_terminal_id(request, x_terminal_id)

    item = next((it for it in _SAMPLE_ITEMS if it.id == id and it.terminal_id == terminal_id), None)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operação/veículo de ID {id} não encontrado no terminal ativo.",
        )

    # Retorna o item com o novo estado simulado
    item_atualizado = item.model_copy(
        update={
            "estado": payload.estado,
            "data_hora": datetime.now(timezone.utc),
        }
    )
    return item_atualizado