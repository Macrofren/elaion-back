"""Serviço de Negócio para Gestão de Tanques de Armazenamento do Terminal."""

from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    ConflitoException,
    ItemNaoEncontradoException,
    RegraNegocioException,
)
from app.domain.models import Tanque, TipoCombustivel
from app.domain.schemas import (
    AtualizarTerminalTanquesRequestDTO,
    TanqueCreateDTO,
    TanqueResponseDTO,
    TanqueUpdateDTO,
)
from app.infra.repositories.tanque_repository import tanque_repository
from app.infra.repositories.terminal_repository import terminal_repository


class TanquesService:
    """Regras de negócio de tanques de armazenamento associados ao terminal ativo."""

    async def listar_tanques(
        self,
        session: AsyncSession,
        terminal_id: int,
        apenas_ativos: bool = False,
        produto: Optional[str] = None,
        produto_id: Optional[int] = None,
    ) -> List[TanqueResponseDTO]:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        filtro_prod = produto or (str(produto_id) if produto_id is not None else None)
        tanques = await tanque_repository.listar_por_terminal(
            session,
            terminal_id,
            apenas_ativos=apenas_ativos,
            produto=filtro_prod,
        )
        return [TanqueResponseDTO.model_validate(t) for t in tanques]

    async def obter_tanque(
        self,
        session: AsyncSession,
        terminal_id: int,
        tanque_id: int,
    ) -> TanqueResponseDTO:
        tanque = await tanque_repository.get_by_id_and_terminal(
            session, terminal_id, tanque_id
        )
        if not tanque:
            raise ItemNaoEncontradoException(
                f"Tanque {tanque_id} não encontrado no terminal {terminal_id}."
            )
        return TanqueResponseDTO.model_validate(tanque)

    async def cadastrar_tanque(
        self,
        session: AsyncSession,
        terminal_id: int,
        dto: TanqueCreateDTO,
    ) -> TanqueResponseDTO:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        identificador_limpo = dto.identificador_tanque.strip().upper()
        if not identificador_limpo:
            raise RegraNegocioException("O identificador do tanque é obrigatório.")

        # Verificar unicidade no terminal
        existente = await tanque_repository.get_by_identificador_terminal(
            session, terminal_id, identificador_limpo
        )
        if existente:
            raise ConflitoException(
                f"Já existe um tanque com o identificador '{identificador_limpo}' cadastrado neste terminal."
            )

        # Regras de capacidade
        cap_operacional = Decimal(str(dto.capacidade_operacional_litros))
        if cap_operacional <= Decimal("0"):
            raise RegraNegocioException("A capacidade operacional deve ser maior que zero.")

        cap_nominal = (
            Decimal(str(dto.capacidade_nominal_litros))
            if dto.capacidade_nominal_litros is not None and dto.capacidade_nominal_litros > 0
            else cap_operacional
        )

        volume_atual = (
            Decimal(str(dto.volume_atual_litros))
            if dto.volume_atual_litros is not None
            else Decimal("0.00")
        )

        novo_tanque = Tanque(
            terminal_id=terminal_id,
            produto=dto.produto,
            produto_id=dto.produto_id,
            identificador_tanque=identificador_limpo,
            capacidade_nominal_litros=cap_nominal,
            capacidade_operacional_litros=cap_operacional,
            volume_atual_litros=volume_atual,
            ativo=dto.ativo,
        )
        salvo = await tanque_repository.salvar(session, novo_tanque)
        await session.commit()
        # Recarregar com relações
        tanque_recarregado = await tanque_repository.get_by_id_and_terminal(
            session, terminal_id, salvo.id
        )
        return TanqueResponseDTO.model_validate(tanque_recarregado)

    async def atualizar_tanque(
        self,
        session: AsyncSession,
        terminal_id: int,
        tanque_id: int,
        dto: TanqueUpdateDTO,
    ) -> TanqueResponseDTO:
        tanque = await tanque_repository.get_by_id_and_terminal(
            session, terminal_id, tanque_id
        )
        if not tanque:
            raise ItemNaoEncontradoException(
                f"Tanque {tanque_id} não encontrado no terminal {terminal_id}."
            )

        if dto.identificador_tanque is not None:
            identificador_limpo = dto.identificador_tanque.strip().upper()
            if not identificador_limpo:
                raise RegraNegocioException("O identificador do tanque não pode ser vazio.")
            if identificador_limpo != tanque.identificador_tanque:
                existente = await tanque_repository.get_by_identificador_terminal(
                    session, terminal_id, identificador_limpo
                )
                if existente and existente.id != tanque_id:
                    raise ConflitoException(
                        f"Já existe outro tanque com o identificador '{identificador_limpo}' neste terminal."
                    )
                tanque.identificador_tanque = identificador_limpo

        if dto.produto is not None and dto.produto != tanque.produto:
            # Se for trocar de produto e houver bicos conectados, verificar consistência
            tem_bicos = await tanque_repository.tem_bicos_vinculados(session, tanque_id)
            if tem_bicos:
                raise RegraNegocioException(
                    "Não é permitido alterar o combustível de um tanque vinculado a bicos operacionais ativos."
                )
            tanque.produto = dto.produto

        if dto.produto_id is not None:
            tanque.produto_id = dto.produto_id

        if dto.capacidade_operacional_litros is not None:
            cap_op = Decimal(str(dto.capacidade_operacional_litros))
            if cap_op <= Decimal("0"):
                raise RegraNegocioException("A capacidade operacional deve ser maior que zero.")
            tanque.capacidade_operacional_litros = cap_op

        if dto.capacidade_nominal_litros is not None:
            cap_nom = Decimal(str(dto.capacidade_nominal_litros))
            if cap_nom <= Decimal("0"):
                raise RegraNegocioException("A capacidade nominal deve ser maior que zero.")
            tanque.capacidade_nominal_litros = cap_nom

        if dto.volume_atual_litros is not None:
            tanque.volume_atual_litros = Decimal(str(dto.volume_atual_litros))

        if dto.ativo is not None:
            tanque.ativo = dto.ativo

        salvo = await tanque_repository.salvar(session, tanque)
        await session.commit()
        tanque_recarregado = await tanque_repository.get_by_id_and_terminal(
            session, terminal_id, salvo.id
        )
        return TanqueResponseDTO.model_validate(tanque_recarregado)

    async def alternar_status_tanque(
        self,
        session: AsyncSession,
        terminal_id: int,
        tanque_id: int,
    ) -> TanqueResponseDTO:
        tanque = await tanque_repository.get_by_id_and_terminal(
            session, terminal_id, tanque_id
        )
        if not tanque:
            raise ItemNaoEncontradoException(
                f"Tanque {tanque_id} não encontrado no terminal {terminal_id}."
            )

        tanque.ativo = not tanque.ativo
        salvo = await tanque_repository.salvar(session, tanque)
        await session.commit()
        tanque_recarregado = await tanque_repository.get_by_id_and_terminal(
            session, terminal_id, salvo.id
        )
        return TanqueResponseDTO.model_validate(tanque_recarregado)

    async def sincronizar_tanques_terminal(
        self,
        session: AsyncSession,
        terminal_id: int,
        payload: AtualizarTerminalTanquesRequestDTO,
    ) -> List[TanqueResponseDTO]:
        """Sincroniza em lote todos os tanques do terminal ativo (Drawer)."""
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        # 1. Validar identificadores duplicados no payload recebido
        identificadores_vistos = set()
        for idx, item in enumerate(payload.tanques, start=1):
            limpo = item.identificador_tanque.strip().upper()
            if not limpo:
                raise RegraNegocioException(f"Linha {idx}: Identificador do tanque não pode ser vazio.")
            if limpo in identificadores_vistos:
                raise RegraNegocioException(
                    f"Identificador duplicado no formulário: '{limpo}'. Cada tanque deve ter identificador único."
                )
            identificadores_vistos.add(limpo)

        # 2. Carregar tanques existentes no banco
        tanques_atuais = await tanque_repository.listar_por_terminal(
            session, terminal_id, apenas_ativos=False
        )
        mapa_atuais = {t.id: t for t in tanques_atuais}

        ids_recebidos = set()

        # 3. Processar cada item do payload (atualizar ou inserir)
        for item in payload.tanques:
            limpo = item.identificador_tanque.strip().upper()
            cap_op = Decimal(str(item.capacidade_operacional_litros))
            cap_nom = (
                Decimal(str(item.capacidade_nominal_litros))
                if item.capacidade_nominal_litros is not None and item.capacidade_nominal_litros > 0
                else cap_op
            )
            vol_atual = (
                Decimal(str(item.volume_atual_litros))
                if item.volume_atual_litros is not None
                else Decimal("0.00")
            )

            if item.id and item.id in mapa_atuais:
                # Tanque existente -> Atualizar
                tanque = mapa_atuais[item.id]
                tanque.identificador_tanque = limpo
                tanque.produto = item.produto
                if item.produto_id is not None:
                    tanque.produto_id = item.produto_id
                tanque.capacidade_operacional_litros = cap_op
                tanque.capacidade_nominal_litros = cap_nom
                tanque.volume_atual_litros = vol_atual
                tanque.ativo = item.ativo
                await tanque_repository.salvar(session, tanque)
                ids_recebidos.add(item.id)
            else:
                # Novo tanque -> Inserir
                novo = Tanque(
                    terminal_id=terminal_id,
                    produto=item.produto,
                    produto_id=item.produto_id,
                    identificador_tanque=limpo,
                    capacidade_nominal_litros=cap_nom,
                    capacidade_operacional_litros=cap_op,
                    volume_atual_litros=vol_atual,
                    ativo=item.ativo,
                )
                salvo = await tanque_repository.salvar(session, novo)
                ids_recebidos.add(salvo.id)

        # 4. Tratar tanques omitidos no payload (Soft delete ou exclusão)
        for t_atual in tanques_atuais:
            if t_atual.id not in ids_recebidos:
                tem_bicos = await tanque_repository.tem_bicos_vinculados(session, t_atual.id)
                if tem_bicos:
                    # Se tem bicos associados, desativa preventivamente
                    t_atual.ativo = False
                    await tanque_repository.salvar(session, t_atual)
                else:
                    await tanque_repository.excluir(session, t_atual)

        await session.commit()

        # Retornar lista completa atualizada
        return await self.listar_tanques(session, terminal_id, apenas_ativos=False)


tanques_service = TanquesService()
