"""
Pacote de segurança da camada de API (HTTP).

Concentra os middlewares/dependências de autenticação (quem é o usuário) e de
autorização (o que ele pode fazer), mantendo a verificação de permissões
modularizada e reutilizável entre os roteadores.
"""

from app.api.security.authentication import obter_usuario_autenticado
from app.api.security.permissions import (
    exige_master,
    exige_permissao,
    exige_qualquer_permissao,
    resolver_terminal_ativo,
)

__all__ = [
    "obter_usuario_autenticado",
    "exige_permissao",
    "exige_qualquer_permissao",
    "exige_master",
    "resolver_terminal_ativo",
]
