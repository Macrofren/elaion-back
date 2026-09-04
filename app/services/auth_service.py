"""
Serviço de Autenticação, Sessão e Primeiro Acesso.

Regras de negócio de login (por CPF ou CNPJ), montagem de perfil, rotação de
tokens e ativação de contas de colaboradores. Sem dependência de bibliotecas web.
"""

import re
from typing import Tuple

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    hash_pin,
    verify_password,
)
from app.domain.exceptions import (
    AcessoNegadoException,
    NaoAutorizadoException,
    RegraNegocioException,
)
from app.domain.models import Usuario
from app.domain.schemas import (
    PrimeiroAcessoConcluirRequest,
    TerminalPermissaoDetalheDTO,
    TerminalVinculoDTO,
    UserProfileResponse,
    UsuarioAutenticadoDTO,
)
from app.infra.repositories.permissao_repository import permissao_repository
from app.infra.repositories.usuario_repository import usuario_repository
from app.infra.repositories.usuario_terminal_repository import usuario_terminal_repository
from app.services.permissoes_service import obter_permissoes_usuario_terminal

STATUS_ATIVO = "ATIVO"
STATUS_PENDENTE = "PENDENTE_ATIVACAO"


def _apenas_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def _claims_do_usuario(usuario: Usuario) -> dict:
    return {
        "sub": str(usuario.id),
        "is_master": usuario.is_master,
        "papel": usuario.papel.value if usuario.papel is not None else None,
        "nome": usuario.nome,
        "cpf": usuario.cpf,
        "cnpj": usuario.cnpj,
        "email": usuario.email,
    }


async def _montar_usuario_autenticado_dto(
    session: AsyncSession, usuario: Usuario
) -> UsuarioAutenticadoDTO:
    terminais_orm = await usuario_terminal_repository.listar_terminais(session, usuario.id)
    terminais = [
        TerminalVinculoDTO(id=t.id, codigo=t.codigo_terminal, nome=t.nome_fantasia)
        for t in terminais_orm
    ]

    permissoes: list[dict] = []
    if not usuario.is_master:
        funcionalidades = await permissao_repository.listar_funcionalidades_usuario(
            session, usuario.id
        )
        permissoes = [
            {
                "id": f.id,
                "modulo": f.modulo.nome if f.modulo else "",
                "funcionalidade": f.nome,
                "chave": f.chave,
                "tipo_acao": f.tipo_acao.value if hasattr(f.tipo_acao, "value") else str(f.tipo_acao),
                "permitido": True,
            }
            for f in funcionalidades
        ]

    return UsuarioAutenticadoDTO(
        id=usuario.id,
        nome=usuario.nome,
        sobrenome=usuario.sobrenome,
        email=usuario.email,
        cpf=usuario.cpf,
        cnpj=usuario.cnpj,
        is_master=usuario.is_master,
        tipo_usuario=usuario.tipo_usuario,
        papel=usuario.papel,
        status_conta=usuario.status_conta,
        foto_perfil_url=usuario.foto_perfil_url,
        precisa_redefinir_senha=False,
        terminais=terminais,
        permissoes=permissoes,
    )



async def _resolver_usuario_por_identificador(
    session: AsyncSession, identificador: str
) -> Usuario | None:
    """Resolve o usuário exclusivamente por CPF (11 díg.) ou CNPJ (14 díg.)."""
    if "@" in identificador:
        raise NaoAutorizadoException("Autenticação permitida apenas por CPF ou CNPJ.")

    digitos = _apenas_digitos(identificador)
    if len(digitos) == 11:
        return await usuario_repository.get_by_cpf(session, digitos)
    if len(digitos) == 14:
        return await usuario_repository.get_by_cnpj(session, digitos)
    raise NaoAutorizadoException("Identificador inválido. Utilize CPF ou CNPJ.")


async def autenticar(
    session: AsyncSession, identificador: str, senha: str
) -> Tuple[str, str, UsuarioAutenticadoDTO]:
    """
    Autentica o usuário por CPF ou CNPJ e retorna (access_token, refresh_token, dto).
    """
    usuario = await _resolver_usuario_por_identificador(session, identificador)
    if usuario is None or not verify_password(senha, usuario.senha_hash):
        raise NaoAutorizadoException("Credenciais inválidas.")

    if not usuario.ativo or usuario.status_conta != STATUS_ATIVO:
        raise AcessoNegadoException("Conta inativa ou pendente de ativação.")

    claims = _claims_do_usuario(usuario)
    access_token = create_access_token(data=claims)
    refresh_token = create_refresh_token(data={"sub": str(usuario.id)})
    dto = await _montar_usuario_autenticado_dto(session, usuario)
    return access_token, refresh_token, dto


async def renovar(session: AsyncSession, refresh_token: str | None) -> Tuple[str, str]:
    """Valida o refresh token e reemite o par de tokens (rotação)."""
    if not refresh_token:
        raise NaoAutorizadoException("Refresh token ausente.")
    try:
        payload = decode_refresh_token(refresh_token)
    except jwt.ExpiredSignatureError:
        raise NaoAutorizadoException("Sessão expirada. Faça login novamente.")
    except jwt.PyJWTError:
        raise NaoAutorizadoException("Refresh token inválido.")

    try:
        usuario_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise NaoAutorizadoException("Refresh token inválido.")

    usuario = await usuario_repository.get_by_id(session, usuario_id)
    if usuario is None or not usuario.ativo or usuario.status_conta != STATUS_ATIVO:
        raise NaoAutorizadoException("Usuário inválido para renovação de sessão.")

    access_token = create_access_token(data=_claims_do_usuario(usuario))
    novo_refresh = create_refresh_token(data={"sub": str(usuario.id)})
    return access_token, novo_refresh


async def montar_perfil(session: AsyncSession, usuario: Usuario) -> UserProfileResponse:
    """Monta o perfil (/auth/me) com terminais e permissões reais por terminal."""
    terminais_orm = await usuario_terminal_repository.listar_terminais(session, usuario.id)
    terminais: list[TerminalPermissaoDetalheDTO] = []
    for t in terminais_orm:
        if usuario.is_master:
            chaves: list[str] = []
        else:
            chaves = sorted(await obter_permissoes_usuario_terminal(session, usuario.id, t.id))
        terminais.append(
            TerminalPermissaoDetalheDTO(
                terminal_id=t.id,
                codigo_terminal=t.codigo_terminal,
                nome_fantasia=t.nome_fantasia,
                permissoes=chaves,
            )
        )

    return UserProfileResponse(
        id=usuario.id,
        nome=usuario.nome,
        sobrenome=usuario.sobrenome,
        cpf=usuario.cpf,
        cnpj=usuario.cnpj,
        email=usuario.email,
        is_master=usuario.is_master,
        tipo_usuario=usuario.tipo_usuario,
        status_conta=usuario.status_conta,
        terminais=terminais,
    )


async def primeiro_acesso_validar(session: AsyncSession, cpf: str, codigo_ativacao: str) -> str:
    """Valida o código ATIV-XXXX pendente para o CPF. Retorna o nome do colaborador."""
    cpf_normalizado = _apenas_digitos(cpf)
    usuario = await usuario_repository.get_by_codigo_ativacao(
        session, cpf_normalizado, codigo_ativacao.strip().upper()
    )
    if usuario is None:
        raise RegraNegocioException("Código de ativação inválido para o CPF informado.")
    if usuario.status_conta != STATUS_PENDENTE:
        raise RegraNegocioException("Esta conta não está pendente de ativação.")
    nome = " ".join(p for p in [usuario.nome, usuario.sobrenome] if p) or "Colaborador"
    return nome


async def primeiro_acesso_concluir(
    session: AsyncSession, payload: PrimeiroAcessoConcluirRequest
) -> None:
    """Cadastra senha pessoal + PIN e ativa a conta do colaborador."""
    cpf_normalizado = _apenas_digitos(payload.cpf)
    usuario = await usuario_repository.get_by_codigo_ativacao(
        session, cpf_normalizado, payload.codigo_ativacao.strip().upper()
    )
    if usuario is None:
        raise RegraNegocioException("Código de ativação inválido para o CPF informado.")
    if usuario.status_conta != STATUS_PENDENTE:
        raise RegraNegocioException("Esta conta não está pendente de ativação.")

    usuario.senha_hash = hash_password(payload.nova_senha)
    usuario.pin_seguranca_hash = hash_pin(payload.pin_seguranca)
    usuario.status_conta = STATUS_ATIVO
    usuario.ativo = True
    usuario.codigo_ativacao = None
    await usuario_repository.salvar(session, usuario)
    await session.commit()
