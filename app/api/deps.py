"""
Dependências compartilhadas da camada de API (FastAPI Depends).

A sessão de banco vive aqui; a autenticação e a verificação de permissões RBAC
foram modularizadas no pacote `app.api.security` e são re-exportadas por
compatibilidade com imports existentes (`from app.api.deps import exige_permissao`).
"""

from app.api.security.authentication import get_db_session, obter_usuario_autenticado
from app.api.security.permissions import (
    exige_master,
    exige_permissao,
    exige_qualquer_permissao,
    resolver_terminal_ativo,
)

__all__ = [
    "get_db_session",
    "obter_usuario_autenticado",
    "exige_permissao",
    "exige_qualquer_permissao",
    "exige_master",
    "resolver_terminal_ativo",
]
