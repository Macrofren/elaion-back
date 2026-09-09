"""Serviço de Negócio para Gestão de Bicos de Operação e Conexão do Terminal."""

from typing import List, Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    ConflitoException,
    ItemNaoEncontradoException,
    RegraNegocioException,
)
from app.domain.models import Bico, Plataforma, Tanque, TipoCombustivel, TipoOperacao, TipoPlataforma
from app.domain.schemas import (
    AtualizarTerminalBicosRequestDTO,
    BicoCreateDTO,
    BicoResponseDTO,
    BicoUpdateDTO,
)
from app.infra.repositories.bico_repository import bico_repository
from app.infra.repositories.plataforma_repository import plataforma_repository
from app.infra.repositories.terminal_repository import terminal_repository


class BicosService:
    """Regras de negócio de bicos de conexão associados ao terminal ativo."""

    async def _validar_tanques(
        self,
        session: AsyncSession,
        terminal_id: int,
        tanque_ids: List[int],
        identificador_bico: str,
    ) -> List[Tanque]:
        """
        Valida que:
        1. Ao menos 1 tanque esteja vinculado.
        2. Todos os tanques pertençam ao terminal ativo.
        (Nota: tanques podem possuir tipos de produtos distintos).
        """
        if not tanque_ids or len(tanque_ids) == 0:
            raise RegraNegocioException(
                f"É obrigatório vincular ao menos 1 tanque ao bico '{identificador_bico}'."
            )

        stmt = (
            select(Tanque)
            .where(
                Tanque.id.in_(tanque_ids),
                Tanque.terminal_id == terminal_id,
            )
        )
        res = await session.execute(stmt)
        tanques_encontrados = res.scalars().all()
        mapa_tanques = {t.id: t for t in tanques_encontrados}

        for tid in tanque_ids:
            if tid not in mapa_tanques:
                raise ItemNaoEncontradoException(
                    f"Tanque {tid} não encontrado no terminal {terminal_id}."
                )

        return list(tanques_encontrados)

    def _validar_compatibilidade_plataforma(
        self,
        plataforma: Plataforma,
        tipo_operacao: TipoOperacao,
        identificador_bico: str,
    ) -> None:
        """
        Valida a coerência da operação do bico com a plataforma:
        - Plataforma CARREGAMENTO: bico deve ser CARREGAMENTO.
        - Plataforma DESCARGA: bico deve ser DESCARGA.
        - Plataforma MISTA: bico pode ser CARREGAMENTO ou DESCARGA.
        """
        if (
            plataforma.tipo == TipoPlataforma.CARREGAMENTO
            and tipo_operacao != TipoOperacao.CARREGAMENTO
        ):
            raise RegraNegocioException(
                f"O bico '{identificador_bico}' foi configurado como DESCARGA, "
                f"mas a plataforma '{plataforma.identificador}' opera exclusivamente CARREGAMENTO."
            )
        if (
            plataforma.tipo == TipoPlataforma.DESCARGA
            and tipo_operacao != TipoOperacao.DESCARGA
        ):
            raise RegraNegocioException(
                f"O bico '{identificador_bico}' foi configurado como CARREGAMENTO, "
                f"mas a plataforma '{plataforma.identificador}' opera exclusivamente DESCARGA."
            )

    async def listar_bicos(
        self,
        session: AsyncSession,
        terminal_id: int,
        apenas_ativos: bool = False,
        plataforma_id: Optional[int] = None,
        tipo_operacao: Optional[TipoOperacao] = None,
        produto: Optional[str] = None,
        produto_id: Optional[int] = None,
    ) -> List[BicoResponseDTO]:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        bicos = await bico_repository.listar_por_terminal(
            session,
            terminal_id,
            apenas_ativos=apenas_ativos,
            plataforma_id=plataforma_id,
            produto=produto,
            produto_id=produto_id,
        )
        if tipo_operacao is not None:
            bicos = [b for b in bicos if b.tipo_operacao == tipo_operacao]

        return [BicoResponseDTO.model_validate(b) for b in bicos]

    async def obter_bico(
        self,
        session: AsyncSession,
        terminal_id: int,
        bico_id: int,
    ) -> BicoResponseDTO:
        bico = await bico_repository.get_by_id_and_terminal(session, terminal_id, bico_id)
        if not bico:
            raise ItemNaoEncontradoException(
                f"Bico {bico_id} não encontrado no terminal {terminal_id}."
            )
        return BicoResponseDTO.model_validate(bico)

    async def cadastrar_bico(
        self,
        session: AsyncSession,
        terminal_id: int,
        dto: BicoCreateDTO,
    ) -> BicoResponseDTO:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        identificador_limpo = dto.identificador_bico.strip().upper()
        if not identificador_limpo:
            raise RegraNegocioException("O identificador do bico é obrigatório.")

        # Verificar duplicidade de identificador no terminal
        existente = await bico_repository.get_by_identificador_terminal(
            session, terminal_id, identificador_limpo
        )
        if existente:
            raise ConflitoException(
                f"Já existe um bico cadastrado com o identificador '{identificador_limpo}' neste terminal."
            )

        # Validar plataforma no terminal
        plataforma = await plataforma_repository.get_by_id_and_terminal(
            session, terminal_id, dto.plataforma_id
        )
        if not plataforma:
            raise ItemNaoEncontradoException(
                f"Plataforma {dto.plataforma_id} não encontrada no terminal {terminal_id}."
            )

        # Validar compatibilidade plataforma x operação
        self._validar_compatibilidade_plataforma(
            plataforma, dto.tipo_operacao, identificador_limpo
        )

        # Validar tanques vinculados (permite produtos distintos)
        await self._validar_tanques(
            session, terminal_id, dto.tanque_ids, identificador_limpo
        )

        novo_bico = Bico(
            terminal_id=terminal_id,
            plataforma_id=dto.plataforma_id,
            tipo_operacao=dto.tipo_operacao,
            produto=dto.produto,
            produto_id=dto.produto_id,
            identificador_bico=identificador_limpo,
            ativo=dto.ativo,
        )
        salvo = await bico_repository.salvar(session, novo_bico)

        # Sincronizar vínculos com os tanques
        await bico_repository.sincronizar_vinculos_tanques(
            session, salvo.id, dto.tanque_ids
        )

        await session.commit()

        # Recarregar com relacionamentos completos
        bico_completo = await bico_repository.get_by_id_and_terminal(
            session, terminal_id, salvo.id
        )
        return BicoResponseDTO.model_validate(bico_completo)

    async def atualizar_bico(
        self,
        session: AsyncSession,
        terminal_id: int,
        bico_id: int,
        dto: BicoUpdateDTO,
    ) -> BicoResponseDTO:
        bico = await bico_repository.get_by_id_and_terminal(session, terminal_id, bico_id)
        if not bico:
            raise ItemNaoEncontradoException(
                f"Bico {bico_id} não encontrado no terminal {terminal_id}."
            )

        novo_identificador = bico.identificador_bico
        if dto.identificador_bico is not None:
            ident_limpo = dto.identificador_bico.strip().upper()
            if not ident_limpo:
                raise RegraNegocioException("O identificador do bico não pode ser vazio.")
            if ident_limpo.lower() != bico.identificador_bico.lower():
                existente = await bico_repository.get_by_identificador_terminal(
                    session, terminal_id, ident_limpo
                )
                if existente and existente.id != bico.id:
                    raise ConflitoException(
                        f"Já existe outro bico com o identificador '{ident_limpo}' neste terminal."
                    )
            novo_identificador = ident_limpo
            bico.identificador_bico = ident_limpo

        plataforma_alvo = bico.plataforma
        if dto.plataforma_id is not None:
            plat = await plataforma_repository.get_by_id_and_terminal(
                session, terminal_id, dto.plataforma_id
            )
            if not plat:
                raise ItemNaoEncontradoException(
                    f"Plataforma {dto.plataforma_id} não encontrada no terminal {terminal_id}."
                )
            plataforma_alvo = plat
            bico.plataforma_id = dto.plataforma_id

        operacao_alvo = dto.tipo_operacao if dto.tipo_operacao is not None else bico.tipo_operacao
        if dto.plataforma_id is not None or dto.tipo_operacao is not None:
            self._validar_compatibilidade_plataforma(
                plataforma_alvo, operacao_alvo, novo_identificador
            )
            bico.tipo_operacao = operacao_alvo

        if dto.produto is not None:
            bico.produto = dto.produto

        if dto.produto_id is not None:
            bico.produto_id = dto.produto_id

        if dto.ativo is not None:
            bico.ativo = dto.ativo

        novos_tanque_ids = (
            dto.tanque_ids if dto.tanque_ids is not None else bico.tanque_ids
        )
        if dto.tanque_ids is not None:
            await self._validar_tanques(
                session, terminal_id, novos_tanque_ids, novo_identificador
            )

        salvo = await bico_repository.salvar(session, bico)

        if dto.tanque_ids is not None:
            await bico_repository.sincronizar_vinculos_tanques(
                session, salvo.id, dto.tanque_ids
            )

        await session.commit()

        bico_completo = await bico_repository.get_by_id_and_terminal(
            session, terminal_id, salvo.id
        )
        return BicoResponseDTO.model_validate(bico_completo)

    async def desativar_bico(
        self,
        session: AsyncSession,
        terminal_id: int,
        bico_id: int,
    ) -> BicoResponseDTO:
        bico = await bico_repository.get_by_id_and_terminal(session, terminal_id, bico_id)
        if not bico:
            raise ItemNaoEncontradoException(
                f"Bico {bico_id} não encontrado no terminal {terminal_id}."
            )

        bico.ativo = False
        salvo = await bico_repository.salvar(session, bico)
        await session.commit()

        bico_completo = await bico_repository.get_by_id_and_terminal(
            session, terminal_id, salvo.id
        )
        return BicoResponseDTO.model_validate(bico_completo)

    async def alternar_status_bico(
        self,
        session: AsyncSession,
        terminal_id: int,
        bico_id: int,
    ) -> BicoResponseDTO:
        bico = await bico_repository.get_by_id_and_terminal(session, terminal_id, bico_id)
        if not bico:
            raise ItemNaoEncontradoException(
                f"Bico {bico_id} não encontrado no terminal {terminal_id}."
            )

        bico.ativo = not bico.ativo
        salvo = await bico_repository.salvar(session, bico)
        await session.commit()

        bico_completo = await bico_repository.get_by_id_and_terminal(
            session, terminal_id, salvo.id
        )
        return BicoResponseDTO.model_validate(bico_completo)

    async def sincronizar_bicos_terminal(
        self,
        session: AsyncSession,
        terminal_id: int,
        payload: AtualizarTerminalBicosRequestDTO,
    ) -> List[BicoResponseDTO]:
        """
        Sincroniza a lista de bicos do terminal (consumido pelo Drawer em lote).
        - Itens existentes são atualizados.
        - Novos itens (sem id ou com id temporário) são criados.
        - Itens omitidos são desativados (soft delete).
        - Valida obrigatoriedade de tanques, unicidade de identificador e compatibilidade da operação com a plataforma.
        """
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        # Validar duplicidade dentro do próprio payload recebido
        identificadores_vistos: Set[str] = set()
        for item in payload.bicos:
            ident_limpo = item.identificador_bico.strip().upper()
            if not ident_limpo:
                raise RegraNegocioException(
                    "Todos os bicos devem possuir um identificador preenchido."
                )
            if ident_limpo in identificadores_vistos:
                raise ConflitoException(
                    f"Identificador '{ident_limpo}' duplicado na lista de bicos enviada."
                )
            identificadores_vistos.add(ident_limpo)

        bicos_atuais = await bico_repository.listar_por_terminal(session, terminal_id)
        mapa_atuais = {b.id: b for b in bicos_atuais}

        ids_processados: Set[int] = set()

        for item in payload.bicos:
            ident_limpo = item.identificador_bico.strip().upper()

            # Validar plataforma
            plataforma = await plataforma_repository.get_by_id_and_terminal(
                session, terminal_id, item.plataforma_id
            )
            if not plataforma:
                raise ItemNaoEncontradoException(
                    f"Plataforma {item.plataforma_id} não encontrada no terminal {terminal_id}."
                )

            # Validar compatibilidade plataforma x operação
            self._validar_compatibilidade_plataforma(
                plataforma, item.tipo_operacao, ident_limpo
            )

            # Validar tanques vinculados (permite produtos distintos)
            await self._validar_tanques(
                session, terminal_id, item.tanque_ids, ident_limpo
            )

            # Se o ID foi informado e existe no banco neste terminal
            if item.id and item.id in mapa_atuais:
                bico = mapa_atuais[item.id]
                bico.identificador_bico = ident_limpo
                bico.plataforma_id = item.plataforma_id
                bico.tipo_operacao = item.tipo_operacao
                bico.produto = item.produto
                if item.produto_id is not None:
                    bico.produto_id = item.produto_id
                bico.ativo = item.ativo
                await bico_repository.salvar(session, bico)
                await bico_repository.sincronizar_vinculos_tanques(
                    session, bico.id, item.tanque_ids
                )
                ids_processados.add(bico.id)
            else:
                # Criar novo bico
                novo_bico = Bico(
                    terminal_id=terminal_id,
                    plataforma_id=item.plataforma_id,
                    tipo_operacao=item.tipo_operacao,
                    produto=item.produto,
                    produto_id=item.produto_id,
                    identificador_bico=ident_limpo,
                    ativo=item.ativo,
                )
                salvo = await bico_repository.salvar(session, novo_bico)
                await bico_repository.sincronizar_vinculos_tanques(
                    session, salvo.id, item.tanque_ids
                )
                ids_processados.add(salvo.id)

        # Desativar (soft delete) os bicos omitidos na requisição
        for bico_atual in bicos_atuais:
            if bico_atual.id not in ids_processados and bico_atual.ativo:
                bico_atual.ativo = False
                await bico_repository.salvar(session, bico_atual)

        await session.commit()

        # Retornar lista completa e atualizada
        bicos_atualizados = await bico_repository.listar_por_terminal(session, terminal_id)
        return [BicoResponseDTO.model_validate(b) for b in bicos_atualizados]


bicos_service = BicosService()
