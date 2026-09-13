"""
Repositório assíncrono para Controle de Acesso e Operações de Pátio (OperacaoVeiculo).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import (
    CODIGOS_ANP_COMBUSTIVEIS,
    NOMES_COMBUSTIVEIS,
    CategoriaProduto,
    Congenere,
    EstadoVeiculo,
    OperacaoCompartimento,
    OperacaoStatusHistorico,
    OperacaoVeiculo,
    Produto,
    StatusOperacao,
    TipoCombustivel,
    TipoOperacao,
    Usuario,
)
from app.infra.repositories.base import BaseRepository


async def obter_ou_criar_produto_por_combustivel(
    session: AsyncSession, tipo: TipoCombustivel
) -> Produto:
    """Obtém ou cadastra dinamicamente o registro na tabela produto correspondente ao TipoCombustivel."""
    codigo_anp = CODIGOS_ANP_COMBUSTIVEIS.get(tipo, f"ANP_{tipo.value}")
    stmt = select(Produto).where(Produto.codigo_anp == codigo_anp)
    res = await session.execute(stmt)
    prod = res.scalars().first()

    if not prod:
        cat = CategoriaProduto.GASOLINA
        val = tipo.value.upper()
        if "DIESEL" in val:
            cat = CategoriaProduto.DIESEL
        elif "ETANOL" in val:
            cat = CategoriaProduto.ETANOL
        elif "BIODIESEL" in val:
            cat = CategoriaProduto.BIODIESEL

        nome = NOMES_COMBUSTIVEIS.get(tipo, tipo.value.replace("_", " ").title())
        prod = Produto(
            codigo_anp=codigo_anp,
            nome=nome,
            categoria=cat,
            unidade_medida="L",
            descricao=f"Produto padrão {nome} cadastrado pelo Controle de Acesso",
        )
        session.add(prod)
        await session.flush()

    return prod


class OperacaoRepository(BaseRepository[OperacaoVeiculo]):
    """Repositório especializado para gestão das operações de veículos no terminal."""

    def __init__(self):
        super().__init__(OperacaoVeiculo)

    async def obter_por_id_detalhado(
        self, session: AsyncSession, operacao_id: int, terminal_id: int
    ) -> Optional[OperacaoVeiculo]:
        """Busca um veículo com todos os relacionamentos carregados (eager loading)."""
        stmt = (
            select(OperacaoVeiculo)
            .where(
                and_(
                    OperacaoVeiculo.id == operacao_id,
                    OperacaoVeiculo.terminal_id == terminal_id,
                )
            )
            .options(
                selectinload(OperacaoVeiculo.compartimentos).selectinload(
                    OperacaoCompartimento.produto
                ),
                selectinload(OperacaoVeiculo.historico_status).selectinload(
                    OperacaoStatusHistorico.usuario
                ),
                selectinload(OperacaoVeiculo.congenere),
                selectinload(OperacaoVeiculo.usuario_registro),
                selectinload(OperacaoVeiculo.usuario_liberacao_saida),
            )
        )
        res = await session.execute(stmt)
        return res.scalars().first()

    async def listar_com_filtros(
        self,
        session: AsyncSession,
        terminal_id: int,
        busca: Optional[str] = None,
        estados: Optional[List[str]] = None,
        operacoes: Optional[List[str]] = None,
        produtos: Optional[List[str]] = None,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        skip: int = 0,
        limit: int = 10,
    ) -> Tuple[List[OperacaoVeiculo], int]:
        """Lista operações paginadas com filtros complexos de portaria."""
        filtros = [OperacaoVeiculo.terminal_id == terminal_id]

        if data_inicio:
            filtros.append(func.date(OperacaoVeiculo.data_hora_entrada) >= data_inicio)
        if data_fim:
            filtros.append(func.date(OperacaoVeiculo.data_hora_entrada) <= data_fim)

        if operacoes:
            ops_normalizadas: List[TipoOperacao] = []
            for op in operacoes:
                op_str = str(op).strip().upper()
                if op_str in ("DESCARGA", "DESCARREGAR"):
                    ops_normalizadas.append(TipoOperacao.DESCARGA)
                elif op_str in ("CARREGAMENTO", "CARREGAR"):
                    ops_normalizadas.append(TipoOperacao.CARREGAMENTO)
            if ops_normalizadas:
                filtros.append(OperacaoVeiculo.tipo_operacao.in_(ops_normalizadas))

        if estados:
            status_set: Set[StatusOperacao] = set()
            for e in estados:
                e_upper = str(e).strip().upper()
                if e_upper in ("FILA", "AGUARDANDO"):
                    status_set.add(StatusOperacao.AGUARDANDO_PORTARIA)
                elif e_upper == "ENTRADA":
                    status_set.add(StatusOperacao.EM_OPERACAO)
                    status_set.add(StatusOperacao.APROVADO_OPERACAO)
                elif e_upper == "COLETA":
                    status_set.add(StatusOperacao.EM_AMOSTRAGEM)
                    status_set.add(StatusOperacao.EM_ANALISE_LAB)
                elif e_upper == "SAIDA":
                    status_set.add(StatusOperacao.CONCLUIDO)
                elif e_upper == "CANCELADO":
                    status_set.add(StatusOperacao.CANCELADO)
                    status_set.add(StatusOperacao.REPROVADO)
            if status_set:
                filtros.append(OperacaoVeiculo.status_operacao.in_(list(status_set)))

        # Subquery para busca textual em múltiplos campos incluindo congênere
        base_query = select(OperacaoVeiculo).where(*filtros)

        if busca and busca.strip():
            termo = f"%{busca.strip().lower()}%"
            base_query = base_query.outerjoin(OperacaoVeiculo.congenere).where(
                or_(
                    func.lower(OperacaoVeiculo.nome_motorista).like(termo),
                    func.lower(OperacaoVeiculo.placa_veiculo).like(termo),
                    func.lower(OperacaoVeiculo.numero_nota_fiscal).like(termo),
                    func.lower(OperacaoVeiculo.nome_transportadora).like(termo),
                    func.lower(Congenere.razao_social).like(termo),
                )
            )

        if produtos:
            prods_upper = [p.strip().upper() for p in produtos if p.strip()]
            if prods_upper:
                # Localizar produtos associados
                codigos_anp_alvo = [
                    CODIGOS_ANP_COMBUSTIVEIS[k]
                    for k in TipoCombustivel
                    if k.value in prods_upper and k in CODIGOS_ANP_COMBUSTIVEIS
                ]
                sub_comp = (
                    select(OperacaoCompartimento.operacao_id)
                    .join(OperacaoCompartimento.produto)
                    .where(
                        or_(
                            Produto.codigo_anp.in_(codigos_anp_alvo),
                            func.upper(Produto.nome).in_(prods_upper),
                        )
                    )
                )
                base_query = base_query.where(OperacaoVeiculo.id.in_(sub_comp))

        # Contagem total
        count_stmt = select(func.count()).select_from(base_query.subquery())
        total_res = await session.execute(count_stmt)
        total = total_res.scalar_one() or 0

        # Carregamento com paginação e ordenação decrescente
        data_stmt = (
            base_query.options(
                selectinload(OperacaoVeiculo.compartimentos).selectinload(
                    OperacaoCompartimento.produto
                ),
                selectinload(OperacaoVeiculo.historico_status).selectinload(
                    OperacaoStatusHistorico.usuario
                ),
                selectinload(OperacaoVeiculo.congenere),
                selectinload(OperacaoVeiculo.usuario_registro),
                selectinload(OperacaoVeiculo.usuario_liberacao_saida),
            )
            .order_by(OperacaoVeiculo.data_hora_entrada.desc(), OperacaoVeiculo.id.desc())
            .offset(skip)
            .limit(limit)
        )

        res = await session.execute(data_stmt)
        itens = list(res.scalars().all())
        return itens, total

    async def obter_contadores(
        self,
        session: AsyncSession,
        terminal_id: int,
        data_inicio: Optional[date] = None,
        data_fim: Optional[date] = None,
        tipo_operacao: Optional[TipoOperacao] = None,
    ) -> Dict[str, int]:
        """Calcula a contagem de veículos agrupada por status/estado para os badges das abas."""
        filtros = [OperacaoVeiculo.terminal_id == terminal_id]

        if data_inicio:
            filtros.append(func.date(OperacaoVeiculo.data_hora_entrada) >= data_inicio)
        if data_fim:
            filtros.append(func.date(OperacaoVeiculo.data_hora_entrada) <= data_fim)
        if tipo_operacao:
            filtros.append(OperacaoVeiculo.tipo_operacao == tipo_operacao)

        stmt = (
            select(OperacaoVeiculo.status_operacao, func.count(OperacaoVeiculo.id))
            .where(*filtros)
            .group_by(OperacaoVeiculo.status_operacao)
        )
        res = await session.execute(stmt)
        counts = {r[0]: r[1] for r in res.all()}

        fila = counts.get(StatusOperacao.AGUARDANDO_PORTARIA, 0)
        entrada = counts.get(StatusOperacao.EM_OPERACAO, 0) + counts.get(
            StatusOperacao.APROVADO_OPERACAO, 0
        )
        coleta = counts.get(StatusOperacao.EM_AMOSTRAGEM, 0) + counts.get(
            StatusOperacao.EM_ANALISE_LAB, 0
        )
        saida = counts.get(StatusOperacao.CONCLUIDO, 0)
        cancelado = counts.get(StatusOperacao.CANCELADO, 0) + counts.get(
            StatusOperacao.REPROVADO, 0
        )
        total = sum(counts.values())

        return {
            "FILA": fila,
            "AGUARDANDO": fila,
            "ENTRADA": entrada,
            "COLETA": coleta,
            "SAIDA": saida,
            "CANCELADO": cancelado,
            "total": total,
        }

    async def criar_operacao_completa(
        self,
        session: AsyncSession,
        terminal_id: int,
        usuario_id: int,
        dados_veiculo: Dict[str, Any],
        compartimentos: List[Dict[str, Any]],
    ) -> OperacaoVeiculo:
        """Cria a operação do veículo com seus compartimentos e primeiro evento na timeline de status."""
        op = OperacaoVeiculo(
            terminal_id=terminal_id,
            congenere_id=dados_veiculo["congenere_id"],
            nome_transportadora=dados_veiculo["transportadora"],
            is_transportadora_propria=dados_veiculo.get("is_propria", False),
            placa_veiculo=dados_veiculo["placa"],
            nome_motorista=dados_veiculo["motorista"],
            numero_nota_fiscal=dados_veiculo["numero_nf"],
            origem_destino=dados_veiculo.get("origem_destino"),
            tipo_operacao=dados_veiculo.get("tipo_operacao", TipoOperacao.DESCARGA),
            status_operacao=StatusOperacao.AGUARDANDO_PORTARIA,
            observacao_geral=dados_veiculo.get("observacao_geral"),
            usuario_registro_id=usuario_id,
        )
        session.add(op)
        await session.flush()

        # Criação dos compartimentos
        for comp in compartimentos:
            prod_enum: TipoCombustivel = comp["produto"]
            produto_db = await obter_ou_criar_produto_por_combustivel(session, prod_enum)

            volume = comp.get("volume_nf") or Decimal("0.00")
            capacidade = comp.get("capacidade_litros") or comp.get("capacidade") or volume

            c = OperacaoCompartimento(
                operacao_id=op.id,
                numero_compartimento=comp["numero"],
                produto_id=produto_db.id,
                volume_nf_litros=Decimal(str(volume)),
                capacidade_compartimento_litros=Decimal(str(capacidade)),
            )
            session.add(c)

        # Primeiro registro de auditoria na timeline
        historico_inicial = OperacaoStatusHistorico(
            operacao_id=op.id,
            status_anterior=None,
            status_novo="FILA",
            usuario_id=usuario_id,
            observacao="Veículo registrado na fila da portaria.",
        )
        session.add(historico_inicial)

        await session.commit()
        return await self.obter_por_id_detalhado(session, op.id, terminal_id)  # type: ignore

    async def registrar_historico_transicao(
        self,
        session: AsyncSession,
        operacao: OperacaoVeiculo,
        status_anterior: str,
        status_novo: str,
        usuario_id: int,
        observacao: Optional[str] = None,
    ) -> OperacaoStatusHistorico:
        """Adiciona um evento de transição na timeline de auditoria."""
        historico = OperacaoStatusHistorico(
            operacao_id=operacao.id,
            status_anterior=status_anterior,
            status_novo=status_novo,
            usuario_id=usuario_id,
            observacao=observacao,
        )
        session.add(historico)
        await session.flush()
        return historico


operacao_repository = OperacaoRepository()
