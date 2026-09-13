"""
Serviço de Negócio para Gestão do Controle de Acesso e Operações de Pátio do Terminal.
Implementa as regras de negócio e a máquina de estados para carga e descarga.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ItemNaoEncontradoException, RegraNegocioException
from app.domain.models import (
    NOMES_COMBUSTIVEIS,
    Congenere,
    EstadoVeiculo,
    OperacaoCompartimento,
    OperacaoVeiculo,
    StatusOperacao,
    TipoCombustivel,
    TipoOperacao,
    Usuario,
)
from app.domain.schemas import (
    AtualizarVeiculoDescargaRequestDTO,
    CompartimentoDetalheDTO,
    ControleAcessoContagensResponseDTO,
    ControleAcessoItemDTO,
    HistoricoEstadoItemDTO,
    NovoVeiculoDescargaRequestDTO,
    PaginatedControleAcessoResponseDTO,
)
from app.infra.repositories.congeneres_repository import congenere_repository
from app.infra.repositories.operacao_repository import (
    obter_ou_criar_produto_por_combustivel,
    operacao_repository,
)


def _montar_dto_item(op: OperacaoVeiculo) -> ControleAcessoItemDTO:
    """Serializa uma entidade OperacaoVeiculo no DTO enriquecido para o frontend."""
    # Lista de combustíveis e totalizadores
    produtos_distintos: List[TipoCombustivel] = []
    detalhes_compartimentos: List[CompartimentoDetalheDTO] = []
    volume_total = Decimal("0.00")
    capacidade_total = Decimal("0.00")

    if op.compartimentos:
        for c in sorted(op.compartimentos, key=lambda x: x.numero_compartimento):
            comb = c.tipo_combustivel
            if comb not in produtos_distintos:
                produtos_distintos.append(comb)

            vol = c.volume_nf_litros or Decimal("0.00")
            cap = c.capacidade_compartimento_litros or vol
            volume_total += vol
            capacidade_total += cap

            nome_prod = NOMES_COMBUSTIVEIS.get(comb, comb.value)
            detalhes_compartimentos.append(
                CompartimentoDetalheDTO(
                    id=c.id,
                    numero=c.numero_compartimento,
                    produto=comb,
                    nome_produto=nome_prod,
                    volume_nf=vol,
                    capacidade=cap,
                )
            )

    # Timeline de auditoria com nomes dos operadores
    historico_dto: List[HistoricoEstadoItemDTO] = []
    if op.historico_status:
        # Ordena cronologicamente
        hist_ordenado = sorted(
            op.historico_status,
            key=lambda h: h.data_hora if h.data_hora else datetime.min.replace(tzinfo=timezone.utc),
        )
        ordem_estados = {"FILA": 1, "AGUARDANDO": 1, "ENTRADA": 2, "COLETA": 3, "SAIDA": 4}
        for h in hist_ordenado:
            nome_usuario = (
                f"{h.usuario.nome} {h.usuario.sobrenome or ''}".strip()
                if (h.usuario and h.usuario.nome)
                else "Operador da Portaria"
            )
            st_ant = str(h.status_anterior).upper() if h.status_anterior else None
            st_novo = str(h.status_novo).upper() if h.status_novo else None
            is_retorno = False
            if st_ant and st_novo and st_novo != "CANCELADO":
                if ordem_estados.get(st_novo, 0) < ordem_estados.get(st_ant, 0):
                    is_retorno = True
                elif any(k in (h.observacao or "").lower() for k in ("retorn", "revers", "volt")):
                    is_retorno = True

            historico_dto.append(
                HistoricoEstadoItemDTO(
                    id=h.id,
                    estado=h.status_novo,
                    status_anterior=h.status_anterior,
                    data_hora=h.data_hora,
                    observacao=h.observacao,
                    usuario=nome_usuario,
                    is_retorno=is_retorno,
                )
            )

    nome_congenere = (
        op.congenere.razao_social if op.congenere else f"Congênere #{op.congenere_id}"
    )

    return ControleAcessoItemDTO(
        id=op.id,
        terminal_id=op.terminal_id,
        estado=op.estado,
        status_operacao=op.status_operacao,
        tipo_operacao=op.tipo_operacao,
        data_hora=op.data_hora_entrada,
        motorista=op.nome_motorista,
        placa=op.placa_veiculo,
        numero_nf=op.numero_nota_fiscal,
        congenere=nome_congenere,
        congenere_id=op.congenere_id,
        transportadora=op.nome_transportadora,
        is_propria=op.is_transportadora_propria,
        observacao_geral=op.observacao_geral,
        motivo_cancelamento=op.motivo_cancelamento,
        produtos=produtos_distintos,
        volume_nf=volume_total,
        capacidade_total=capacidade_total if capacidade_total > 0 else volume_total,
        numero_compartimentos=len(detalhes_compartimentos),
        compartimentos=detalhes_compartimentos,
        historico_estados=historico_dto,
    )


class OperacaoService:
    """Regras de negócio e transições de estado para o Controle de Acesso."""

    async def listar_veiculos(
        self,
        session: AsyncSession,
        terminal_id: int,
        busca: Optional[str] = None,
        estados: Optional[List[str]] = None,
        operacoes: Optional[List[str]] = None,
        produtos: Optional[List[str]] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> PaginatedControleAcessoResponseDTO:
        """Listagem paginada e filtrada de veículos na portaria."""
        d_inicio: Optional[date] = None
        d_fim: Optional[date] = None

        if data_inicio:
            try:
                d_inicio = date.fromisoformat(data_inicio.split("T")[0])
            except ValueError:
                pass
        if data_fim:
            try:
                d_fim = date.fromisoformat(data_fim.split("T")[0])
            except ValueError:
                pass

        skip = (page - 1) * page_size
        itens, total = await operacao_repository.listar_com_filtros(
            session=session,
            terminal_id=terminal_id,
            busca=busca,
            estados=estados,
            operacoes=operacoes,
            produtos=produtos,
            data_inicio=d_inicio,
            data_fim=d_fim,
            skip=skip,
            limit=page_size,
        )

        dtos = [_montar_dto_item(item) for item in itens]
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        return PaginatedControleAcessoResponseDTO(
            items=dtos,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def obter_contagens(
        self,
        session: AsyncSession,
        terminal_id: int,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        tipo_operacao_str: Optional[str] = None,
    ) -> ControleAcessoContagensResponseDTO:
        """Obtém as contagens consolidadas para as abas (FILA, ENTRADA, COLETA, SAIDA, CANCELADO, TOTAL)."""
        d_inicio: Optional[date] = None
        d_fim: Optional[date] = None
        if data_inicio:
            try:
                d_inicio = date.fromisoformat(data_inicio.split("T")[0])
            except ValueError:
                pass
        if data_fim:
            try:
                d_fim = date.fromisoformat(data_fim.split("T")[0])
            except ValueError:
                pass

        tipo_op: Optional[TipoOperacao] = None
        if tipo_operacao_str:
            op_upper = tipo_operacao_str.strip().upper()
            if op_upper in ("DESCARGA", "DESCARREGAR"):
                tipo_op = TipoOperacao.DESCARGA
            elif op_upper in ("CARREGAMENTO", "CARREGAR"):
                tipo_op = TipoOperacao.CARREGAMENTO

        counts = await operacao_repository.obter_contadores(
            session=session,
            terminal_id=terminal_id,
            data_inicio=d_inicio,
            data_fim=d_fim,
            tipo_operacao=tipo_op,
        )

        return ControleAcessoContagensResponseDTO(**counts)

    async def obter_detalhes_veiculo(
        self, session: AsyncSession, operacao_id: int, terminal_id: int
    ) -> ControleAcessoItemDTO:
        """Retorna os dados completos do veículo para o drawer lateral de detalhes."""
        op = await operacao_repository.obter_por_id_detalhado(
            session, operacao_id, terminal_id
        )
        if not op:
            raise ItemNaoEncontradoException(
                f"Veículo/Operação #{operacao_id} não encontrado no terminal ativo."
            )
        return _montar_dto_item(op)

    async def cadastrar_veiculo_descarga(
        self,
        session: AsyncSession,
        terminal_id: int,
        usuario_id: int,
        dto: NovoVeiculoDescargaRequestDTO,
    ) -> ControleAcessoItemDTO:
        """Cadastra um novo caminhão de descarga com estado inicial FILA."""
        # 1. Validar congênere
        congenere = await congenere_repository.get_by_id(session, dto.congenere_id)
        if not congenere or congenere.terminal_id != terminal_id:
            raise RegraNegocioException(
                f"A distribuidora congênere #{dto.congenere_id} não pertence ao terminal ativo ou não existe.",
                status_code=422,
            )

        # 2. Validar compartimentos
        compartimentos_in = dto.compartimentos or []
        if not compartimentos_in:
            raise RegraNegocioException(
                "O veículo deve possuir ao menos 1 compartimento especificado com produto e volume.",
                status_code=422,
            )

        dados_veiculo = {
            "placa": dto.placa,
            "motorista": dto.motorista.strip(),
            "numero_nf": dto.numero_nf.strip(),
            "congenere_id": dto.congenere_id,
            "transportadora": dto.transportadora.strip(),
            "is_propria": dto.is_propria,
            "tipo_operacao": dto.tipo_operacao or TipoOperacao.DESCARGA,
            "observacao_geral": dto.observacao_geral.strip() if dto.observacao_geral else None,
        }

        comps_dict = [
            {
                "numero": c.numero,
                "produto": c.produto,
                "volume_nf": c.volume_nf,
                "capacidade_litros": c.capacidade_litros or max(c.volume_nf, Decimal("10000.00")),
            }
            for c in compartimentos_in
        ]

        op = await operacao_repository.criar_operacao_completa(
            session=session,
            terminal_id=terminal_id,
            usuario_id=usuario_id,
            dados_veiculo=dados_veiculo,
            compartimentos=comps_dict,
        )

        return _montar_dto_item(op)

    async def atualizar_veiculo_fila(
        self,
        session: AsyncSession,
        operacao_id: int,
        terminal_id: int,
        usuario_id: int,
        dto: AtualizarVeiculoDescargaRequestDTO,
    ) -> ControleAcessoItemDTO:
        """Permite editar os dados cadastrais do veículo exclusivamente enquanto estiver no estado FILA."""
        op = await operacao_repository.obter_por_id_detalhado(session, operacao_id, terminal_id)
        if not op:
            raise ItemNaoEncontradoException(f"Veículo #{operacao_id} não encontrado.")

        if op.estado != EstadoVeiculo.FILA:
            raise RegraNegocioException(
                f"Apenas veículos no estado FILA podem ser editados (estado atual: {op.estado.value}).",
                status_code=422,
            )

        # Atualizar dados básicos
        if dto.motorista:
            op.nome_motorista = dto.motorista.strip()
        if dto.placa:
            op.placa_veiculo = dto.placa
        if dto.numero_nf:
            op.numero_nota_fiscal = dto.numero_nf.strip()
        if dto.congenere_id is not None:
            congenere = await congenere_repository.get_by_id(session, dto.congenere_id)
            if not congenere or congenere.terminal_id != terminal_id:
                raise RegraNegocioException(
                    f"Distribuidora congênere #{dto.congenere_id} inválida para este terminal.",
                    status_code=422,
                )
            op.congenere_id = dto.congenere_id
        if dto.transportadora:
            op.nome_transportadora = dto.transportadora.strip()
        if dto.is_propria is not None:
            op.is_transportadora_propria = dto.is_propria
        if dto.tipo_operacao is not None:
            op.tipo_operacao = dto.tipo_operacao
        if dto.observacao_geral is not None:
            op.observacao_geral = dto.observacao_geral.strip()

        # Atualizar compartimentos se informados
        if dto.compartimentos:
            # Remove anteriores
            await session.execute(
                delete(OperacaoCompartimento).where(
                    OperacaoCompartimento.operacao_id == op.id
                )
            )
            for c in dto.compartimentos:
                prod_db = await obter_ou_criar_produto_por_combustivel(session, c.produto)
                vol = c.volume_nf
                cap = c.capacidade_litros or max(vol, Decimal("10000.00"))
                novo_comp = OperacaoCompartimento(
                    operacao_id=op.id,
                    numero_compartimento=c.numero,
                    produto_id=prod_db.id,
                    volume_nf_litros=Decimal(str(vol)),
                    capacidade_compartimento_litros=Decimal(str(cap)),
                )
                session.add(novo_comp)

        await session.commit()
        op_atualizado = await operacao_repository.obter_por_id_detalhado(session, op.id, terminal_id)
        return _montar_dto_item(op_atualizado)  # type: ignore

    async def transitar_estado(
        self,
        session: AsyncSession,
        operacao_id: int,
        terminal_id: int,
        usuario: Usuario,
        novo_estado: EstadoVeiculo,
        motivo: Optional[str] = None,
        bafometro_resultado: Optional[str] = None,
        bafometro_valor: Optional[Decimal] = None,
    ) -> ControleAcessoItemDTO:
        """
        Executa a máquina de estados para transições de veículos na portaria.
        Regras:
        - FILA -> ENTRADA: Exige bafômetro NEGATIVO (0.00 mg/L).
        - FILA -> COLETA: REJEITADA! A portaria não transiciona direto de fila para coleta.
        - ENTRADA -> SAIDA: Caso feliz da portaria.
        - ENTRADA -> COLETA: Transição operacional de amostragem no pátio.
        - COLETA -> SAIDA: Liberação após coleta.
        - Rollbacks: COLETA -> ENTRADA e ENTRADA -> FILA (exigem justificativa).
        - CANCELADO: Permitido de FILA ou ENTRADA com motivo.
        - SAIDA / CANCELADO: Estados terminais imutáveis.
        """
        op = await operacao_repository.obter_por_id_detalhado(session, operacao_id, terminal_id)
        if not op:
            raise ItemNaoEncontradoException(f"Veículo/Operação #{operacao_id} não encontrado.")

        estado_atual = op.estado

        # 1. Validação de estados terminais
        if estado_atual in (EstadoVeiculo.SAIDA, EstadoVeiculo.CANCELADO):
            raise RegraNegocioException(
                f"Veículo já se encontra em estado final ({estado_atual.value}) e não pode ter o estado alterado.",
                status_code=422,
            )

        usuario_id = usuario.id

        # 2. Transição para ENTRADA
        if novo_estado == EstadoVeiculo.ENTRADA:
            if estado_atual not in (EstadoVeiculo.FILA, EstadoVeiculo.COLETA):
                raise RegraNegocioException(
                    f"Transição para ENTRADA permitida somente a partir de FILA ou rollback de COLETA (atual: {estado_atual.value}).",
                    status_code=422,
                )

            # Se vindo da FILA, valida teste de bafômetro
            if estado_atual == EstadoVeiculo.FILA:
                if (
                    (bafometro_resultado and bafometro_resultado.upper() == "POSITIVO")
                    or (bafometro_valor and bafometro_valor > Decimal("0.00"))
                ):
                    raise RegraNegocioException(
                        "Alcoolemia positiva detectada no teste do bafômetro! Acesso do motorista bloqueado.",
                        status_code=422,
                    )

            op.status_operacao = StatusOperacao.EM_OPERACAO
            obs = motivo or "Entrada liberada na portaria com bafômetro 0,00 mg/L."
            await operacao_repository.registrar_historico_transicao(
                session=session,
                operacao=op,
                status_anterior=estado_atual.value,
                status_novo="ENTRADA",
                usuario_id=usuario_id,
                observacao=obs,
            )

        # 3. Transição para COLETA (Amostragem)
        elif novo_estado == EstadoVeiculo.COLETA:
            # REGRA EXPRESSA DO USUÁRIO: "desconsidere o caso fila -> coleta no controle de acesso"
            if estado_atual == EstadoVeiculo.FILA:
                raise RegraNegocioException(
                    "Transição direta da FILA para COLETA não é permitida no Controle de Acesso. "
                    "O veículo deve primeiro dar ENTRADA no terminal.",
                    status_code=422,
                )
            if estado_atual != EstadoVeiculo.ENTRADA:
                raise RegraNegocioException(
                    f"Avanço para COLETA permitido somente a partir de ENTRADA (atual: {estado_atual.value}).",
                    status_code=422,
                )

            op.status_operacao = StatusOperacao.EM_AMOSTRAGEM
            obs = motivo or "Veículo encaminhado para amostragem/triagem de combustíveis."
            await operacao_repository.registrar_historico_transicao(
                session=session,
                operacao=op,
                status_anterior=estado_atual.value,
                status_novo="COLETA",
                usuario_id=usuario_id,
                observacao=obs,
            )

        # 4. Transição para SAIDA (Caso Feliz Final)
        elif novo_estado == EstadoVeiculo.SAIDA:
            if estado_atual not in (EstadoVeiculo.ENTRADA, EstadoVeiculo.COLETA):
                raise RegraNegocioException(
                    f"Liberação de SAÍDA permitida apenas após ENTRADA ou COLETA concluída (atual: {estado_atual.value}).",
                    status_code=422,
                )

            op.status_operacao = StatusOperacao.CONCLUIDO
            op.data_hora_saida = datetime.now(timezone.utc)
            op.usuario_liberacao_saida_id = usuario_id
            obs = motivo or "Veículo liberado e operação de descarga finalizada na portaria."
            await operacao_repository.registrar_historico_transicao(
                session=session,
                operacao=op,
                status_anterior=estado_atual.value,
                status_novo="SAIDA",
                usuario_id=usuario_id,
                observacao=obs,
            )

        # 5. Rollback para FILA (ou AGUARDANDO)
        elif novo_estado == EstadoVeiculo.FILA:
            if estado_atual != EstadoVeiculo.ENTRADA:
                raise RegraNegocioException(
                    f"Retorno para FILA permitido somente a partir de ENTRADA (atual: {estado_atual.value}).",
                    status_code=422,
                )
            op.status_operacao = StatusOperacao.AGUARDANDO_PORTARIA
            obs = motivo or "Veículo retornado para a fila da portaria."
            await operacao_repository.registrar_historico_transicao(
                session=session,
                operacao=op,
                status_anterior=estado_atual.value,
                status_novo="FILA",
                usuario_id=usuario_id,
                observacao=obs,
            )

        # 6. Transição para CANCELADO
        elif novo_estado == EstadoVeiculo.CANCELADO:
            if estado_atual not in (EstadoVeiculo.FILA, EstadoVeiculo.ENTRADA):
                raise RegraNegocioException(
                    f"Cancelamento não permitido para veículo no estado {estado_atual.value}.",
                    status_code=422,
                )
            op.status_operacao = StatusOperacao.CANCELADO
            op.motivo_cancelamento = motivo or "Cancelamento registrado pelo operador."
            await operacao_repository.registrar_historico_transicao(
                session=session,
                operacao=op,
                status_anterior=estado_atual.value,
                status_novo="CANCELADO",
                usuario_id=usuario_id,
                observacao=op.motivo_cancelamento,
            )

        else:
            raise RegraNegocioException(
                f"Estado de destino não reconhecido: {novo_estado}.",
                status_code=422,
            )

        await session.commit()
        op_atualizado = await operacao_repository.obter_por_id_detalhado(session, op.id, terminal_id)
        return _montar_dto_item(op_atualizado)  # type: ignore

    async def retornar_estado_anterior(
        self,
        session: AsyncSession,
        operacao_id: int,
        terminal_id: int,
        usuario: Usuario,
        motivo: str,
    ) -> ControleAcessoItemDTO:
        """Realiza o rollback de estado com justificativa obrigatória."""
        op = await operacao_repository.obter_por_id_detalhado(session, operacao_id, terminal_id)
        if not op:
            raise ItemNaoEncontradoException(f"Veículo #{operacao_id} não encontrado.")

        if not motivo or len(motivo.strip()) < 3:
            raise RegraNegocioException(
                "O motivo da reversão de estado é obrigatório (mínimo 3 caracteres).",
                status_code=422,
            )

        estado_atual = op.estado
        if estado_atual == EstadoVeiculo.COLETA:
            destino = EstadoVeiculo.ENTRADA
        elif estado_atual == EstadoVeiculo.ENTRADA:
            destino = EstadoVeiculo.FILA
        else:
            raise RegraNegocioException(
                f"Não é possível reverter o estado de um veículo no estado {estado_atual.value}.",
                status_code=422,
            )

        return await self.transitar_estado(
            session=session,
            operacao_id=operacao_id,
            terminal_id=terminal_id,
            usuario=usuario,
            novo_estado=destino,
            motivo=motivo.strip(),
        )

    async def cancelar_acesso(
        self,
        session: AsyncSession,
        operacao_id: int,
        terminal_id: int,
        usuario: Usuario,
        motivo: Optional[str] = None,
    ) -> ControleAcessoItemDTO:
        """Cancela o acesso do veículo na portaria."""
        return await self.transitar_estado(
            session=session,
            operacao_id=operacao_id,
            terminal_id=terminal_id,
            usuario=usuario,
            novo_estado=EstadoVeiculo.CANCELADO,
            motivo=motivo,
        )


operacao_service = OperacaoService()
