"""
Serviço de Gestão de Colaboradores do Terminal (pelo Gestor Master).

Catálogo de permissões, criação de colaborador (com emissão de ATIV-XXXX),
listagem e autorização de redefinição presencial (emissão de LIB-XXXX).
Sem dependência de bibliotecas web.
"""

import re
import secrets
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.core.security import hash_password
from app.domain.exceptions import (
    ConflitoException,
    ItemNaoEncontradoException,
    RegraNegocioException,
)
from app.domain.models import ModuloFuncionalidade, PapelUsuario, TipoUsuario, UsuarioPermissao, UsuarioTerminal
from app.domain.schemas import (
    AutorizarRedefinicaoResponse,
    CatalogoPermissoesModuloDTO,
    CriarUsuarioTerminalRequest,
    CriarUsuarioTerminalResponse,
    PermissaoFuncionalDTO,
    UsuarioTerminalResumoDTO,
)
from app.infra.repositories.permissao_repository import permissao_repository
from app.infra.repositories.terminal_repository import terminal_repository
from app.infra.repositories.usuario_repository import usuario_repository
from app.infra.repositories.usuario_terminal_repository import usuario_terminal_repository
from app.services.codigos_service import gerar_codigo_ativacao, gerar_codigo_liberacao
from app.services.permissoes_service import invalidar_cache_permissoes

STATUS_PENDENTE = "PENDENTE_ATIVACAO"


def _apenas_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def _nome_completo(nome: str | None, sobrenome: str | None) -> str:
    partes = [p for p in [nome, sobrenome] if p]
    return " ".join(partes) if partes else "Sem Nome"


async def _garantir_terminal(session: AsyncSession, terminal_id: int) -> None:
    if await terminal_repository.get_by_id(session, terminal_id) is None:
        raise ItemNaoEncontradoException(f"Terminal {terminal_id} não encontrado.")


async def catalogo_permissoes(
    session: AsyncSession, terminal_id: int
) -> List[CatalogoPermissoesModuloDTO]:
    """Retorna a árvore de módulos contratados + funcionalidades do terminal."""
    await _garantir_terminal(session, terminal_id)
    modulos = await permissao_repository.listar_modulos_contratados(session, terminal_id)
    return [
        CatalogoPermissoesModuloDTO(
            modulo_id=m.id,
            codigo_modulo=m.codigo,
            nome_modulo=m.nome,
            funcionalidades=[
                PermissaoFuncionalDTO(
                    id=f.id,
                    chave=f.chave,
                    nome=f.nome,
                    funcionalidade=f.nome,
                    modulo=m.nome,
                    tipo_acao=f.tipo_acao,
                    permitido=True,
                )
                for f in sorted(m.funcionalidades, key=lambda x: x.id)
            ],
        )
        for m in modulos
    ]


async def listar_colaboradores(
    session: AsyncSession, terminal_id: int
) -> List[UsuarioTerminalResumoDTO]:
    """Lista os colaboradores vinculados ao terminal com telefone e permissões."""
    await _garantir_terminal(session, terminal_id)
    usuarios = await usuario_terminal_repository.listar_usuarios_do_terminal(session, terminal_id)

    # 1. Carregar permissões explícitas dos usuários vinculados a este terminal
    stmt = (
        select(UsuarioTerminal.usuario_id, ModuloFuncionalidade)
        .join(UsuarioPermissao, UsuarioPermissao.usuario_terminal_id == UsuarioTerminal.id)
        .join(ModuloFuncionalidade, ModuloFuncionalidade.id == UsuarioPermissao.funcionalidade_id)
        .where(
            UsuarioTerminal.terminal_id == terminal_id,
            UsuarioTerminal.ativo.is_(True),
            UsuarioPermissao.permitido.is_(True),
        )
        .options(joinedload(ModuloFuncionalidade.modulo))
        .order_by(ModuloFuncionalidade.id)
    )
    result = await session.execute(stmt)

    user_perms_map: dict[int, list[PermissaoFuncionalDTO]] = defaultdict(list)
    for uid, f in result.all():
        user_perms_map[uid].append(
            PermissaoFuncionalDTO(
                id=f.id,
                chave=f.chave,
                nome=f.nome,
                funcionalidade=f.nome,
                modulo=f.modulo.nome if f.modulo else "SIRAC",
                tipo_acao=f.tipo_acao.value if hasattr(f.tipo_acao, "value") else str(f.tipo_acao),
                permitido=True,
            )
        )

    # 2. Carregar módulos contratados para dar full access aos usuários Master
    modulos = await permissao_repository.listar_modulos_contratados(session, terminal_id)
    master_perms = [
        PermissaoFuncionalDTO(
            id=f.id,
            chave=f.chave,
            nome=f.nome,
            funcionalidade=f.nome,
            modulo=m.nome,
            tipo_acao=f.tipo_acao.value if hasattr(f.tipo_acao, "value") else str(f.tipo_acao),
            permitido=True,
        )
        for m in modulos
        for f in sorted(m.funcionalidades, key=lambda x: x.id)
    ]

    return [
        UsuarioTerminalResumoDTO(
            id=u.id,
            nome_completo=_nome_completo(u.nome, u.sobrenome),
            cpf=u.cpf,
            email=u.email,
            telefone=u.telefone,
            foto_perfil_url=u.foto_perfil_url,
            papel=u.papel,
            status_conta=u.status_conta,
            ativo=u.ativo,
            is_master=u.is_master,
            permissoes=master_perms if u.is_master else user_perms_map.get(u.id, []),
        )
        for u in usuarios
    ]


async def criar_colaborador(
    session: AsyncSession,
    terminal_id: int,
    payload: CriarUsuarioTerminalRequest,
) -> CriarUsuarioTerminalResponse:
    """
    Cria um colaborador vinculado ao terminal, atribui permissões do SIRAC e
    emite o código de ativação (ATIV-XXXX) para o Primeiro Acesso.
    """
    await _garantir_terminal(session, terminal_id)

    # Validações de papel específicas
    if payload.papel == PapelUsuario.QUIMICO and payload.laboratorio is None:
        raise RegraNegocioException("Colaborador com papel 'Químico' exige um laboratório vinculado.")
    if payload.papel == PapelUsuario.CONGENERE and payload.congenere is None:
        raise RegraNegocioException("Colaborador com papel 'Congênere' exige uma congênere vinculada.")

    cpf = _apenas_digitos(payload.cpf)
    if await usuario_repository.get_by_cpf(session, cpf):
        raise ConflitoException("Já existe um usuário cadastrado com este CPF.")

    # Resolve as permissões informadas (IDs ou chaves) para funcionalidades reais
    funcionalidades = await permissao_repository.resolver_funcionalidades(session, payload.permissoes)
    if payload.permissoes and len(funcionalidades) != len(set(map(str, payload.permissoes))):
        # Alguma permissão informada não existe no catálogo
        encontradas = {f.id for f in funcionalidades} | {f.chave for f in funcionalidades}
        invalidas = [p for p in payload.permissoes if p not in encontradas and str(p) not in map(str, encontradas)]
        if invalidas:
            raise RegraNegocioException(f"Permissões inválidas ou inexistentes: {invalidas}.")

    # Gera código de ativação único
    codigo_ativacao = await gerar_codigo_ativacao(
        lambda c: usuario_repository.codigo_ativacao_existe(session, c)
    )

    # Cria o usuário (senha inutilizável até o Primeiro Acesso)
    novo = await usuario_repository.criar(
        session,
        {
            "nome": payload.nome,
            "sobrenome": payload.sobrenome,
            "cpf": cpf,
            "email": payload.email,
            "telefone": payload.telefone,
            "foto_perfil_url": payload.foto_perfil_url,
            "papel": payload.papel,
            "senha_hash": hash_password(secrets.token_urlsafe(32)),
            "codigo_ativacao": codigo_ativacao,
            "status_conta": STATUS_PENDENTE,
            "tipo_usuario": TipoUsuario.USUARIO_TERMINAL,
            "is_master": False,
            "ativo": True,
        },
    )


    vinculo = await usuario_terminal_repository.criar_vinculo(session, novo.id, terminal_id)

    if funcionalidades:
        await permissao_repository.atribuir_permissoes(
            session, vinculo.id, [f.id for f in funcionalidades]
        )

    await session.commit()

    # Invalidação em tempo real do cache de permissões
    await invalidar_cache_permissoes(usuario_id=novo.id, terminal_id=terminal_id)

    return CriarUsuarioTerminalResponse(
        usuario_id=novo.id,
        nome_completo=_nome_completo(novo.nome, novo.sobrenome),
        cpf=novo.cpf,
        papel=novo.papel or payload.papel,
        status_conta=novo.status_conta,
        codigo_ativacao=codigo_ativacao,
    )


async def autorizar_redefinicao(
    session: AsyncSession,
    terminal_id: int,
    usuario_id: int,
) -> AutorizarRedefinicaoResponse:
    """
    Fase 1 do Handshake: gera e persiste um código de liberação (LIB-XXXX)
    temporário para a redefinição presencial de senha do colaborador.
    """
    await _garantir_terminal(session, terminal_id)

    vinculo = await usuario_terminal_repository.get_vinculo(session, usuario_id, terminal_id)
    if vinculo is None:
        raise ItemNaoEncontradoException(
            f"Colaborador {usuario_id} não está vinculado ao terminal {terminal_id}."
        )

    usuario = await usuario_repository.get_by_id(session, usuario_id)
    if usuario is None:
        raise ItemNaoEncontradoException(f"Colaborador {usuario_id} não encontrado.")

    codigo_liberacao = await gerar_codigo_liberacao(
        lambda c: usuario_repository.codigo_liberacao_existe(session, c)
    )
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=settings.LIB_CODIGO_EXPIRE_MINUTES)

    usuario.codigo_liberacao_master = codigo_liberacao
    usuario.liberacao_expira_em = expira_em
    await usuario_repository.salvar(session, usuario)
    await session.commit()

    return AutorizarRedefinicaoResponse(
        usuario_id=usuario.id,
        nome_colaborador=_nome_completo(usuario.nome, usuario.sobrenome),
        codigo_liberacao=codigo_liberacao,
        expira_em_minutos=settings.LIB_CODIGO_EXPIRE_MINUTES,
    )
