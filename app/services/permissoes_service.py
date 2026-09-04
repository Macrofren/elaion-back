"""
Serviço de Domínio para Consulta e Gestão de Permissões RBAC (Opção 2).
Intermedeia o acesso entre o banco de dados relacional e a camada de cache híbrido.
"""

from typing import Optional, Set
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import permissoes_cache
from app.domain.models import ModuloFuncionalidade, UsuarioPermissao, UsuarioTerminal


def gerar_cache_key(usuario_id: int, terminal_id: int) -> str:
    """Retorna a chave canônica de cache de permissões do usuário em um terminal."""
    return f"permissoes:{usuario_id}:{terminal_id}"


async def obter_permissoes_usuario_terminal(
    session: AsyncSession,
    usuario_id: int,
    terminal_id: int,
) -> Set[str]:
    """
    Obtém o conjunto de chaves de permissão do usuário para o terminal especificado.
    Aplica estratégia Cache-Aside (Cache Híbrido com Fallback ao Banco Relacional).
    """
    cache_key = gerar_cache_key(usuario_id, terminal_id)

    # 1. Tenta recuperar da camada de cache
    cached = await permissoes_cache.get(cache_key)
    if cached is not None:
        # Se for o marcador de usuário sem permissões, retorna set vazio
        if cached == {"__VAZIO__"}:
            return set()
        return cached

    # 2. Cache-miss: Consulta estruturada no PostgreSQL via SQLAlchemy Async
    stmt = (
        select(ModuloFuncionalidade.chave)
        .join(UsuarioPermissao, UsuarioPermissao.funcionalidade_id == ModuloFuncionalidade.id)
        .join(UsuarioTerminal, UsuarioTerminal.id == UsuarioPermissao.usuario_terminal_id)
        .where(
            UsuarioTerminal.usuario_id == usuario_id,
            UsuarioTerminal.terminal_id == terminal_id,
            UsuarioTerminal.ativo.is_(True),
            UsuarioPermissao.permitido.is_(True),
        )
    )
    result = await session.execute(stmt)
    permissoes: Set[str] = set(result.scalars().all())

    # 3. Popula a camada de cache com TTL configurado (default: 15 min)
    await permissoes_cache.set(cache_key, permissoes)

    return permissoes


async def invalidar_cache_permissoes(usuario_id: int, terminal_id: Optional[int] = None) -> None:
    """
    Invalida o cache de permissões em tempo real.
    - Se informado o terminal_id: invalida a entrada específica do terminal.
    - Se omitido: invalida todas as entradas daquele usuário em todos os seus terminais.
    """
    if terminal_id is not None:
        await permissoes_cache.delete(gerar_cache_key(usuario_id, terminal_id))
    else:
        await permissoes_cache.delete_pattern(f"permissoes:{usuario_id}:")
