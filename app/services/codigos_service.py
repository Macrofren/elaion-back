"""
Serviço de geração de códigos operacionais (ATIV-XXXX / LIB-XXXX).

Gera sufixos alfanuméricos aleatórios seguros com verificação de unicidade
delegada a uma função de checagem (callback) fornecida pelo chamador.
"""

import secrets
import string
from typing import Awaitable, Callable

from app.core.config import settings

_ALFABETO = string.ascii_uppercase + string.digits


def _gerar_sufixo(tamanho: int = 4) -> str:
    return "".join(secrets.choice(_ALFABETO) for _ in range(tamanho))


async def gerar_codigo_unico(
    prefixo: str,
    existe: Callable[[str], Awaitable[bool]],
    tamanho: int = 4,
    max_tentativas: int = 10,
) -> str:
    """
    Gera um código '<PREFIXO>-<SUFIXO>' garantindo unicidade via callback `existe`.
    """
    for _ in range(max_tentativas):
        codigo = f"{prefixo}-{_gerar_sufixo(tamanho)}"
        if not await existe(codigo):
            return codigo
    # Fallback praticamente impossível de colidir
    return f"{prefixo}-{_gerar_sufixo(tamanho + 4)}"


async def gerar_codigo_ativacao(existe: Callable[[str], Awaitable[bool]]) -> str:
    return await gerar_codigo_unico(settings.CODIGO_ATIVACAO_PREFIX, existe)


async def gerar_codigo_liberacao(existe: Callable[[str], Awaitable[bool]]) -> str:
    return await gerar_codigo_unico(settings.CODIGO_LIBERACAO_PREFIX, existe)
