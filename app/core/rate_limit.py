"""
Rate limiting leve para endpoints sensíveis (login, primeiro acesso, redefinição).

Mitiga ataques de força bruta com uma janela deslizante em memória, thread-safe
via asyncio.Lock. É por processo (cada worker mantém sua própria contagem); para
um limite global e distribuído, plugar um backend Redis é o próximo passo natural.
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import HTTPException, Request, status


class RateLimiter:
    """Janela deslizante em memória: no máximo `max_hits` eventos por `window`."""

    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def permitir(self, chave: str, max_hits: int, window_seconds: int) -> bool:
        """Registra uma tentativa e informa se ela está dentro do limite."""
        agora = time.monotonic()
        limite_inferior = agora - window_seconds
        async with self._lock:
            eventos = self._hits[chave]
            while eventos and eventos[0] < limite_inferior:
                eventos.popleft()
            if len(eventos) >= max_hits:
                return False
            eventos.append(agora)
            # Evita crescimento indefinido de chaves ociosas.
            if not eventos:
                self._hits.pop(chave, None)
            return True


rate_limiter = RateLimiter()


def _client_ip(request: Request) -> str:
    """Resolve o IP de origem considerando proxies confiáveis (X-Forwarded-For)."""
    encaminhado = request.headers.get("x-forwarded-for")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else "desconhecido"


def limite_requisicoes(escopo: str, max_hits: int, window_seconds: int):
    """
    Fábrica de dependência FastAPI que aplica rate limiting por IP de origem.
    Uso: `dependencies=[Depends(limite_requisicoes("login", 10, 60))]`.
    """

    async def _dependency(request: Request) -> None:
        chave = f"rl:{escopo}:{_client_ip(request)}"
        permitido = await rate_limiter.permitir(chave, max_hits, window_seconds)
        if not permitido:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Muitas tentativas em um curto período. Aguarde e tente novamente.",
                headers={"Retry-After": str(window_seconds)},
            )

    return _dependency
