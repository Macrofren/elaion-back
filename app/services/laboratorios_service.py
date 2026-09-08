"""Serviço de Negócio para Gestão de Laboratórios do Terminal."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    ConflitoException,
    ItemNaoEncontradoException,
    RegraNegocioException,
)
from app.domain.models import Laboratorio
from app.domain.schemas import (
    AtualizarTerminalLaboratoriosRequestDTO,
    LaboratorioCreateDTO,
    LaboratorioResponseDTO,
    LaboratorioUpdateDTO,
)
from app.infra.repositories.laboratorio_repository import laboratorio_repository
from app.infra.repositories.terminal_repository import terminal_repository


class LaboratoriosService:
    """Regras de negócio de laboratórios associados ao terminal ativo."""

    async def listar_laboratorios(
        self,
        session: AsyncSession,
        terminal_id: int,
        apenas_ativos: bool = False,
    ) -> List[LaboratorioResponseDTO]:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        labs = await laboratorio_repository.listar_por_terminal(
            session, terminal_id, apenas_ativos=apenas_ativos
        )
        return [LaboratorioResponseDTO.model_validate(lab) for lab in labs]

    async def obter_laboratorio(
        self,
        session: AsyncSession,
        terminal_id: int,
        laboratorio_id: int,
    ) -> LaboratorioResponseDTO:
        lab = await laboratorio_repository.get_by_id_and_terminal(
            session, terminal_id, laboratorio_id
        )
        if not lab:
            raise ItemNaoEncontradoException(
                f"Laboratório {laboratorio_id} não encontrado no terminal {terminal_id}."
            )
        return LaboratorioResponseDTO.model_validate(lab)

    async def cadastrar_laboratorio(
        self,
        session: AsyncSession,
        terminal_id: int,
        dto: LaboratorioCreateDTO,
    ) -> LaboratorioResponseDTO:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        nome_limpo = dto.nome.strip()
        if not nome_limpo:
            raise RegraNegocioException("O nome do laboratório é obrigatório.")

        # Verificar se já existe com o mesmo nome neste terminal
        existente = await laboratorio_repository.get_by_nome_terminal(
            session, terminal_id, nome_limpo
        )
        if existente:
            raise ConflitoException(
                f"Já existe um laboratório com o nome '{nome_limpo}' cadastrado neste terminal."
            )

        codigo_limpo = dto.codigo.strip() if dto.codigo and dto.codigo.strip() else None

        novo_lab = Laboratorio(
            terminal_id=terminal_id,
            nome=nome_limpo,
            codigo=codigo_limpo,
            is_proprio=dto.is_proprio,
            ativo=dto.ativo,
        )
        salvo = await laboratorio_repository.salvar(session, novo_lab)
        await session.commit()
        await session.refresh(salvo)
        return LaboratorioResponseDTO.model_validate(salvo)

    async def atualizar_laboratorio(
        self,
        session: AsyncSession,
        terminal_id: int,
        laboratorio_id: int,
        dto: LaboratorioUpdateDTO,
    ) -> LaboratorioResponseDTO:
        lab = await laboratorio_repository.get_by_id_and_terminal(
            session, terminal_id, laboratorio_id
        )
        if not lab:
            raise ItemNaoEncontradoException(
                f"Laboratório {laboratorio_id} não encontrado no terminal {terminal_id}."
            )

        if dto.nome is not None:
            nome_limpo = dto.nome.strip()
            if not nome_limpo:
                raise RegraNegocioException("O nome do laboratório não pode ser vazio.")
            if nome_limpo.lower() != lab.nome.lower():
                existente = await laboratorio_repository.get_by_nome_terminal(
                    session, terminal_id, nome_limpo
                )
                if existente and existente.id != lab.id:
                    raise ConflitoException(
                        f"Já existe outro laboratório com o nome '{nome_limpo}' neste terminal."
                    )
            lab.nome = nome_limpo

        if dto.codigo is not None:
            lab.codigo = dto.codigo.strip() if dto.codigo.strip() else None

        if dto.is_proprio is not None:
            lab.is_proprio = dto.is_proprio

        if dto.ativo is not None:
            lab.ativo = dto.ativo

        salvo = await laboratorio_repository.salvar(session, lab)
        await session.commit()
        await session.refresh(salvo)
        return LaboratorioResponseDTO.model_validate(salvo)

    async def desativar_laboratorio(
        self,
        session: AsyncSession,
        terminal_id: int,
        laboratorio_id: int,
    ) -> LaboratorioResponseDTO:
        """
        Desativação lógica do laboratório para preservação de integridade referencial
        com relatórios e laudos históricos de analise_amostra.
        """
        lab = await laboratorio_repository.get_by_id_and_terminal(
            session, terminal_id, laboratorio_id
        )
        if not lab:
            raise ItemNaoEncontradoException(
                f"Laboratório {laboratorio_id} não encontrado no terminal {terminal_id}."
            )

        lab.ativo = False
        salvo = await laboratorio_repository.salvar(session, lab)
        await session.commit()
        await session.refresh(salvo)
        return LaboratorioResponseDTO.model_validate(salvo)

    async def alternar_status_laboratorio(
        self,
        session: AsyncSession,
        terminal_id: int,
        laboratorio_id: int,
    ) -> LaboratorioResponseDTO:
        lab = await laboratorio_repository.get_by_id_and_terminal(
            session, terminal_id, laboratorio_id
        )
        if not lab:
            raise ItemNaoEncontradoException(
                f"Laboratório {laboratorio_id} não encontrado no terminal {terminal_id}."
            )

        lab.ativo = not lab.ativo
        salvo = await laboratorio_repository.salvar(session, lab)
        await session.commit()
        await session.refresh(salvo)
        return LaboratorioResponseDTO.model_validate(salvo)

    async def sincronizar_laboratorios_terminal(
        self,
        session: AsyncSession,
        terminal_id: int,
        payload: AtualizarTerminalLaboratoriosRequestDTO,
    ) -> List[LaboratorioResponseDTO]:
        """
        Sincroniza a lista de laboratórios do terminal (usado pelo Drawer em lote).
        - Itens existentes são atualizados.
        - Novos itens (sem id ou com id temporário) são criados.
        - Itens omitidos são desativados (soft delete).
        """
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        labs_atuais = await laboratorio_repository.listar_por_terminal(session, terminal_id)
        mapa_atuais = {l.id: l for l in labs_atuais}

        ids_processados = set()

        for item in payload.laboratorios:
            nome_limpo = item.nome.strip()
            if not nome_limpo:
                raise RegraNegocioException("Todos os laboratórios devem conter um nome preenchido.")

            codigo_limpo = item.codigo.strip() if item.codigo and item.codigo.strip() else None

            # Se o ID foi informado e existe no banco neste terminal
            if item.id and item.id in mapa_atuais:
                lab = mapa_atuais[item.id]
                lab.nome = nome_limpo
                lab.codigo = codigo_limpo
                lab.is_proprio = item.is_proprio
                lab.ativo = item.ativo
                await laboratorio_repository.salvar(session, lab)
                ids_processados.add(lab.id)
            else:
                # Criar novo laboratório
                novo_lab = Laboratorio(
                    terminal_id=terminal_id,
                    nome=nome_limpo,
                    codigo=codigo_limpo,
                    is_proprio=item.is_proprio,
                    ativo=item.ativo,
                )
                salvo = await laboratorio_repository.salvar(session, novo_lab)
                ids_processados.add(salvo.id)

        # Desativar os que não foram enviados na lista (soft delete)
        for lab_atual in labs_atuais:
            if lab_atual.id not in ids_processados and lab_atual.ativo:
                lab_atual.ativo = False
                await laboratorio_repository.salvar(session, lab_atual)

        await session.commit()

        # Retornar lista completa e atualizada
        labs_atualizados = await laboratorio_repository.listar_por_terminal(session, terminal_id)
        return [LaboratorioResponseDTO.model_validate(lab) for lab in labs_atualizados]


laboratorios_service = LaboratoriosService()
