"""Serviço de Negócio para Gestão de Plataformas de Operação do Terminal."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    ConflitoException,
    ItemNaoEncontradoException,
    RegraNegocioException,
)
from app.domain.models import Plataforma, TipoPlataforma
from app.domain.schemas import (
    AtualizarTerminalPlataformasRequestDTO,
    PlataformaCreateDTO,
    PlataformaResponseDTO,
    PlataformaUpdateDTO,
)
from app.infra.repositories.plataforma_repository import plataforma_repository
from app.infra.repositories.terminal_repository import terminal_repository


class PlataformasService:
    """Regras de negócio de plataformas de operação associadas ao terminal ativo."""

    async def listar_plataformas(
        self,
        session: AsyncSession,
        terminal_id: int,
        apenas_ativos: bool = False,
        tipo: Optional[TipoPlataforma] = None,
    ) -> List[PlataformaResponseDTO]:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        plataformas = await plataforma_repository.listar_por_terminal(
            session, terminal_id, apenas_ativos=apenas_ativos, tipo=tipo
        )
        return [PlataformaResponseDTO.model_validate(p) for p in plataformas]

    async def obter_plataforma(
        self,
        session: AsyncSession,
        terminal_id: int,
        plataforma_id: int,
    ) -> PlataformaResponseDTO:
        plataforma = await plataforma_repository.get_by_id_and_terminal(
            session, terminal_id, plataforma_id
        )
        if not plataforma:
            raise ItemNaoEncontradoException(
                f"Plataforma {plataforma_id} não encontrada no terminal {terminal_id}."
            )
        return PlataformaResponseDTO.model_validate(plataforma)

    async def cadastrar_plataforma(
        self,
        session: AsyncSession,
        terminal_id: int,
        dto: PlataformaCreateDTO,
    ) -> PlataformaResponseDTO:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        identificador_limpo = dto.identificador.strip().upper()
        if not identificador_limpo:
            raise RegraNegocioException("O identificador da plataforma é obrigatório.")

        # Verificar se já existe com o mesmo identificador neste terminal
        existente = await plataforma_repository.get_by_identificador_terminal(
            session, terminal_id, identificador_limpo
        )
        if existente:
            raise ConflitoException(
                f"Já existe uma plataforma com o identificador '{identificador_limpo}' cadastrada neste terminal."
            )

        nome_limpo = dto.nome.strip() if dto.nome and dto.nome.strip() else None

        nova_plat = Plataforma(
            terminal_id=terminal_id,
            identificador=identificador_limpo,
            nome=nome_limpo,
            tipo=dto.tipo,
            ativo=dto.ativo,
        )
        salvo = await plataforma_repository.salvar(session, nova_plat)
        await session.commit()
        await session.refresh(salvo)
        return PlataformaResponseDTO.model_validate(salvo)

    async def atualizar_plataforma(
        self,
        session: AsyncSession,
        terminal_id: int,
        plataforma_id: int,
        dto: PlataformaUpdateDTO,
    ) -> PlataformaResponseDTO:
        plataforma = await plataforma_repository.get_by_id_and_terminal(
            session, terminal_id, plataforma_id
        )
        if not plataforma:
            raise ItemNaoEncontradoException(
                f"Plataforma {plataforma_id} não encontrada no terminal {terminal_id}."
            )

        if dto.identificador is not None:
            identificador_limpo = dto.identificador.strip().upper()
            if not identificador_limpo:
                raise RegraNegocioException("O identificador da plataforma não pode ser vazio.")
            if identificador_limpo.lower() != plataforma.identificador.lower():
                existente = await plataforma_repository.get_by_identificador_terminal(
                    session, terminal_id, identificador_limpo
                )
                if existente and existente.id != plataforma.id:
                    raise ConflitoException(
                        f"Já existe outra plataforma com o identificador '{identificador_limpo}' neste terminal."
                    )
            plataforma.identificador = identificador_limpo

        if dto.nome is not None:
            plataforma.nome = dto.nome.strip() if dto.nome.strip() else None

        if dto.tipo is not None:
            plataforma.tipo = dto.tipo

        if dto.ativo is not None:
            plataforma.ativo = dto.ativo

        salvo = await plataforma_repository.salvar(session, plataforma)
        await session.commit()
        await session.refresh(salvo)
        return PlataformaResponseDTO.model_validate(salvo)

    async def desativar_plataforma(
        self,
        session: AsyncSession,
        terminal_id: int,
        plataforma_id: int,
    ) -> PlataformaResponseDTO:
        """
        Desativação lógica da plataforma para preservação de integridade referencial
        com bicos e operações históricas vinculadas.
        """
        plataforma = await plataforma_repository.get_by_id_and_terminal(
            session, terminal_id, plataforma_id
        )
        if not plataforma:
            raise ItemNaoEncontradoException(
                f"Plataforma {plataforma_id} não encontrada no terminal {terminal_id}."
            )

        plataforma.ativo = False
        salvo = await plataforma_repository.salvar(session, plataforma)
        await session.commit()
        await session.refresh(salvo)
        return PlataformaResponseDTO.model_validate(salvo)

    async def alternar_status_plataforma(
        self,
        session: AsyncSession,
        terminal_id: int,
        plataforma_id: int,
    ) -> PlataformaResponseDTO:
        plataforma = await plataforma_repository.get_by_id_and_terminal(
            session, terminal_id, plataforma_id
        )
        if not plataforma:
            raise ItemNaoEncontradoException(
                f"Plataforma {plataforma_id} não encontrada no terminal {terminal_id}."
            )

        plataforma.ativo = not plataforma.ativo
        salvo = await plataforma_repository.salvar(session, plataforma)
        await session.commit()
        await session.refresh(salvo)
        return PlataformaResponseDTO.model_validate(salvo)

    async def sincronizar_plataformas_terminal(
        self,
        session: AsyncSession,
        terminal_id: int,
        payload: AtualizarTerminalPlataformasRequestDTO,
    ) -> List[PlataformaResponseDTO]:
        """
        Sincroniza a lista de plataformas do terminal (consumido pelo Drawer em lote).
        - Itens existentes são atualizados.
        - Novos itens (sem id ou com id temporário) são criados.
        - Itens omitidos são desativados (soft delete).
        - Valida unicidade de identificador no lote e no banco.
        """
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        # Validar duplicidade dentro do próprio payload recebido
        identificadores_vistos = set()
        for item in payload.plataformas:
            ident_limpo = item.identificador.strip().upper()
            if not ident_limpo:
                raise RegraNegocioException("Todas as plataformas devem possuir um identificador preenchido.")
            if ident_limpo in identificadores_vistos:
                raise ConflitoException(
                    f"Identificador '{ident_limpo}' duplicado na lista de plataformas enviada."
                )
            identificadores_vistos.add(ident_limpo)

        plataformas_atuais = await plataforma_repository.listar_por_terminal(session, terminal_id)
        mapa_atuais = {p.id: p for p in plataformas_atuais}

        ids_processados = set()

        for item in payload.plataformas:
            ident_limpo = item.identificador.strip().upper()
            nome_limpo = item.nome.strip() if item.nome and item.nome.strip() else None

            # Se o ID foi informado e existe no banco neste terminal
            if item.id and item.id in mapa_atuais:
                plat = mapa_atuais[item.id]
                plat.identificador = ident_limpo
                plat.nome = nome_limpo
                plat.tipo = item.tipo
                plat.ativo = item.ativo
                await plataforma_repository.salvar(session, plat)
                ids_processados.add(plat.id)
            else:
                # Criar nova plataforma
                nova_plat = Plataforma(
                    terminal_id=terminal_id,
                    identificador=ident_limpo,
                    nome=nome_limpo,
                    tipo=item.tipo,
                    ativo=item.ativo,
                )
                salvo = await plataforma_repository.salvar(session, nova_plat)
                ids_processados.add(salvo.id)

        # Desativar (soft delete) as que não foram enviadas na lista
        for plat_atual in plataformas_atuais:
            if plat_atual.id not in ids_processados and plat_atual.ativo:
                plat_atual.ativo = False
                await plataforma_repository.salvar(session, plat_atual)

        await session.commit()

        # Retornar lista completa e atualizada
        plataformas_atualizadas = await plataforma_repository.listar_por_terminal(session, terminal_id)
        return [PlataformaResponseDTO.model_validate(p) for p in plataformas_atualizadas]


plataformas_service = PlataformasService()
