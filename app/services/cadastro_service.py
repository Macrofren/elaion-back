"""
Serviço de Cadastro e Onboarding do Terminal (assinatura comercial).

Regras de negócio da validação do código de assinatura e do registro atômico de
Organização + Terminal + Usuário Master.
"""

import re
import secrets
import string
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.domain.exceptions import ConflitoException, RegraNegocioException
from app.domain.models import Organizacao, TipoUsuario, Usuario
from app.domain.schemas import RegistrationPayload
from app.infra.repositories.convite_repository import convite_repository
from app.infra.repositories.organizacao_repository import organizacao_repository
from app.infra.repositories.terminal_repository import terminal_repository
from app.infra.repositories.usuario_repository import usuario_repository
from app.infra.repositories.usuario_terminal_repository import usuario_terminal_repository


def _apenas_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def _normalizar_codigo(codigo: str) -> str:
    return (codigo or "").strip().upper()


def _gerar_codigo_terminal() -> str:
    sufixo = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"TERM-{sufixo}"


async def _validar_convite(session: AsyncSession, codigo: str):
    convite = await convite_repository.get_by_codigo(session, codigo)
    if convite is None:
        raise RegraNegocioException("Código de ativação inválido.")
    if convite.utilizado:
        raise RegraNegocioException("Código de ativação já foi utilizado.")
    if convite.expira_em is not None:
        agora = datetime.now(timezone.utc)
        expira_em = convite.expira_em
        if expira_em.tzinfo is None:
            expira_em = expira_em.replace(tzinfo=timezone.utc)
        if agora > expira_em:
            raise RegraNegocioException("Código de ativação expirado.")
    return convite


async def validar_codigo(session: AsyncSession, codigo: str) -> None:
    """Valida o código de assinatura comercial (Step 1 do Onboarding)."""
    await _validar_convite(session, _normalizar_codigo(codigo))


async def registrar(session: AsyncSession, payload: RegistrationPayload) -> Organizacao:
    """
    Registra Organização + Terminal + Usuário Master em uma única transação e
    consome o convite de cadastro. Retorna a Organização criada.
    """
    codigo = _normalizar_codigo(payload.codigo_ativacao)
    convite = await _validar_convite(session, codigo)

    org_cnpj = _apenas_digitos(payload.organizacao.cnpj)
    if await organizacao_repository.get_by_cnpj(session, org_cnpj):
        raise ConflitoException("Já existe uma organização cadastrada com este CNPJ.")

    master_cnpj = _apenas_digitos(payload.usuario_master.cnpj)
    if await usuario_repository.get_by_cnpj(session, master_cnpj):
        raise ConflitoException("Já existe um usuário master cadastrado com este CNPJ.")

    # 1. Organização
    organizacao = await organizacao_repository.criar(
        session,
        razao_social=payload.organizacao.razao_social,
        nome_fantasia=payload.organizacao.nome_fantasia or payload.organizacao.razao_social,
        cnpj=org_cnpj,
    )

    # 2. Terminal (dados do Step 3)
    terminal_dto = payload.terminal
    terminal = await terminal_repository.criar(
        session,
        {
            "organizacao_id": organizacao.id,
            "codigo_terminal": _gerar_codigo_terminal(),
            "razao_social": terminal_dto.razao_social,
            "nome_fantasia": terminal_dto.nome_fantasia or terminal_dto.razao_social,
            "cnpj": _apenas_digitos(terminal_dto.cnpj),
            "inscricao_estadual": terminal_dto.inscricao_estadual,
            "telefone": terminal_dto.telefone,
            "telefone_financeiro": terminal_dto.telefone_financeiro,
            "email": terminal_dto.email,
            "email_financeiro": terminal_dto.email_financeiro,
            "cep": _apenas_digitos(terminal_dto.cep),
            "logradouro": terminal_dto.logradouro,
            "numero": terminal_dto.numero,
            "complemento": terminal_dto.complemento,
            "bairro": terminal_dto.bairro,
            "cidade": terminal_dto.cidade,
            "uf": terminal_dto.uf,
        },
    )

    # 3. Usuário Master — criado a partir dos dados do terminal (razão social),
    #    autenticado por CNPJ. Não possui nome/sobrenome/CPF.
    master = await usuario_repository.criar(
        session,
        {
            "nome": terminal_dto.razao_social,
            "sobrenome": None,
            "cpf": None,
            "cnpj": master_cnpj,
            "email": terminal_dto.email,
            "telefone": terminal_dto.telefone,
            "senha_hash": hash_password(payload.usuario_master.senha),
            "is_master": True,
            "tipo_usuario": TipoUsuario.USUARIO_TERMINAL,
            "status_conta": "ATIVO",
            "ativo": True,
        },
    )

    # 4. Vínculo master ↔ terminal
    await usuario_terminal_repository.criar_vinculo(session, master.id, terminal.id)

    # 5. Consome o convite
    await convite_repository.marcar_utilizado(session, convite, organizacao.id)

    await session.commit()
    await session.refresh(organizacao)
    return organizacao
