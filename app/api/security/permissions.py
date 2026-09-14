"""
Autorização (AuthZ) da camada de API — verificação de permissões RBAC (Opção 2).

Fatores de dependência modulares e reutilizáveis para proteger rotas antes da
execução dos services (regras de negócio). Todos resolvem o usuário via JWT,
aplicam bypass de Master e resolvem o terminal ativo (Path Param > Header).
"""

from typing import Iterable, List, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.security.authentication import get_db_session, obter_usuario_autenticado
from app.domain.models import Usuario
from app.infra.repositories.usuario_terminal_repository import usuario_terminal_repository
from app.services.permissoes_service import obter_permissoes_usuario_terminal


def resolver_terminal_ativo(request: Request, x_terminal_id: Optional[int]) -> Optional[int]:
    """
    Resolve o terminal ativo da requisição, priorizando o Path Param `terminal_id`
    sobre o Header `X-Terminal-ID`.
    """
    terminal_id_raw = request.path_params.get("terminal_id")
    if terminal_id_raw is not None:
        try:
            return int(terminal_id_raw)
        except (ValueError, TypeError):
            pass
    return x_terminal_id


def _resolver_terminal_obrigatorio(request: Request, x_terminal_id: Optional[int]) -> int:
    """Resolve o terminal ativo exigindo sua presença (path param ou header)."""
    terminal_id = resolver_terminal_ativo(request, x_terminal_id)
    if terminal_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Identificador de terminal não informado na requisição. "
                "Forneça o path parameter ou o header 'X-Terminal-ID'."
            ),
        )
    return terminal_id


async def _garantir_vinculo_terminal(
    session: AsyncSession, usuario: Usuario, terminal_id: int
) -> None:
    """
    Garante o isolamento multi-tenant: o usuário (inclusive Master) só pode operar
    em terminais aos quais possui vínculo ATIVO. Sem esta checagem, um Master de uma
    organização poderia acessar terminais de outra via header X-Terminal-ID.
    """
    vinculo = await usuario_terminal_repository.get_vinculo(session, usuario.id, terminal_id)
    if vinculo is None or not vinculo.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Acesso negado: usuário sem vínculo ativo com o terminal {terminal_id}."
            ),
        )


def exige_permissao(chave_funcionalidade: str):
    """
    Fator de dependência: exige UMA permissão funcional específica no terminal ativo.
    Master possui bypass total.
    """

    async def _dependency(
        request: Request,
        usuario: Usuario = Depends(obter_usuario_autenticado),
        x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
        session: AsyncSession = Depends(get_db_session),
    ) -> Usuario:
        terminal_id = _resolver_terminal_obrigatorio(request, x_terminal_id)
        # Isolamento multi-tenant: vale inclusive para o Master.
        await _garantir_vinculo_terminal(session, usuario, terminal_id)

        if usuario.is_master:
            return usuario

        permissoes = await obter_permissoes_usuario_terminal(session, usuario.id, terminal_id)
        if chave_funcionalidade not in permissoes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acesso negado: a funcionalidade requer a permissão "
                    f"'{chave_funcionalidade}' no terminal {terminal_id}."
                ),
            )
        return usuario

    return _dependency


def exige_qualquer_permissao(chaves_funcionalidades: Iterable[str]):
    """
    Fator de dependência: exige AO MENOS UMA das permissões informadas no terminal
    ativo. Master possui bypass total.
    """
    chaves: List[str] = list(chaves_funcionalidades)

    async def _dependency(
        request: Request,
        usuario: Usuario = Depends(obter_usuario_autenticado),
        x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
        session: AsyncSession = Depends(get_db_session),
    ) -> Usuario:
        terminal_id = _resolver_terminal_obrigatorio(request, x_terminal_id)
        # Isolamento multi-tenant: vale inclusive para o Master.
        await _garantir_vinculo_terminal(session, usuario, terminal_id)

        if usuario.is_master:
            return usuario

        permissoes = await obter_permissoes_usuario_terminal(session, usuario.id, terminal_id)
        if not any(chave in permissoes for chave in chaves):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Acesso negado: a funcionalidade requer ao menos uma das permissões "
                    f"{chaves} no terminal {terminal_id}."
                ),
            )
        return usuario

    return _dependency


def exige_master():
    """
    Fator de dependência: exige que o usuário autenticado seja Master (gestor).
    """

    async def _dependency(
        usuario: Usuario = Depends(obter_usuario_autenticado),
    ) -> Usuario:
        if not usuario.is_master:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso restrito ao Gestor Master do terminal.",
            )
        return usuario

    return _dependency
