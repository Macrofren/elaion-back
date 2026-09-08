"""Serviço de Negócio para Gestão e Configuração do Terminal."""

import re
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import (
    ConflitoException,
    ItemNaoEncontradoException,
    RegraNegocioException,
)
from app.domain.schemas import TerminalDetalheDTO, TerminalGeralUpdateDTO
from app.infra.repositories.terminal_repository import terminal_repository


def _sanitizar_digitos(valor: Optional[str]) -> Optional[str]:
    if not valor:
        return None
    return re.sub(r"\D", "", valor)


class TerminalService:
    """Regras de negócio e persistência para Terminal."""

    async def obter_terminal(
        self, session: AsyncSession, terminal_id: int
    ) -> TerminalDetalheDTO:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")
        return TerminalDetalheDTO.model_validate(terminal)

    async def atualizar_geral(
        self, session: AsyncSession, terminal_id: int, dto: TerminalGeralUpdateDTO
    ) -> TerminalDetalheDTO:
        terminal = await terminal_repository.get_by_id(session, terminal_id)
        if not terminal:
            raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")

        dados_atualizar = {}

        if dto.codigo_terminal is not None:
            novo_codigo = dto.codigo_terminal.strip().upper()
            if not novo_codigo:
                raise RegraNegocioException("O Código do Terminal não pode ser vazio.")
            if novo_codigo != terminal.codigo_terminal:
                outro = await terminal_repository.get_by_codigo_org(
                    session, terminal.organizacao_id, novo_codigo
                )
                if outro and outro.id != terminal.id:
                    raise ConflitoException(
                        f"Já existe outro terminal com o código '{novo_codigo}' nesta organização."
                    )
                dados_atualizar["codigo_terminal"] = novo_codigo

        if dto.razao_social is not None:
            rs = dto.razao_social.strip()
            if not rs:
                raise RegraNegocioException("A Razão Social é obrigatória.")
            dados_atualizar["razao_social"] = rs

        if dto.nome_fantasia is not None:
            nf = dto.nome_fantasia.strip()
            dados_atualizar["nome_fantasia"] = nf if nf else dados_atualizar.get("razao_social", terminal.razao_social)

        if dto.cnpj is not None:
            clean_cnpj = _sanitizar_digitos(dto.cnpj)
            if not clean_cnpj or len(clean_cnpj) != 14:
                raise RegraNegocioException("CNPJ inválido. Deve conter exatamente 14 dígitos.")
            dados_atualizar["cnpj"] = clean_cnpj

        if dto.inscricao_estadual is not None:
            dados_atualizar["inscricao_estadual"] = dto.inscricao_estadual.strip()

        if dto.telefone is not None:
            dados_atualizar["telefone"] = _sanitizar_digitos(dto.telefone)

        if dto.telefone_financeiro is not None:
            dados_atualizar["telefone_financeiro"] = _sanitizar_digitos(dto.telefone_financeiro)

        if dto.email is not None:
            dados_atualizar["email"] = dto.email.strip().lower() if dto.email.strip() else None

        if dto.email_financeiro is not None:
            dados_atualizar["email_financeiro"] = dto.email_financeiro.strip().lower() if dto.email_financeiro.strip() else None

        if dto.cep is not None:
            dados_atualizar["cep"] = _sanitizar_digitos(dto.cep)

        if dto.logradouro is not None:
            dados_atualizar["logradouro"] = dto.logradouro.strip() or None

        if dto.numero is not None:
            dados_atualizar["numero"] = dto.numero.strip() or None

        if dto.complemento is not None:
            dados_atualizar["complemento"] = dto.complemento.strip() or None

        if dto.bairro is not None:
            dados_atualizar["bairro"] = dto.bairro.strip() or None

        if dto.cidade is not None:
            dados_atualizar["cidade"] = dto.cidade.strip() or None

        if dto.uf is not None:
            dados_atualizar["uf"] = dto.uf.strip().upper() or None

        if dto.ativo is not None:
            dados_atualizar["ativo"] = dto.ativo

        atualizado = await terminal_repository.atualizar(session, terminal, dados_atualizar)
        await session.commit()
        await session.refresh(atualizado)
        return TerminalDetalheDTO.model_validate(atualizado)


terminal_service = TerminalService()
