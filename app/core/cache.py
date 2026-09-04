"""
Mecanismo de Cache Híbrido de Alta Performance para Permissões RBAC (Opção 2).
Fornece armazenamento em memória assíncrono e thread-safe com TTL (Time-To-Live),
com suporte transparente para Redis caso configurado no ambiente (.env).
"""

import asyncio
import time
from typing import Any, Dict, NamedTuple, Optional, Set
from app.core.config import settings


class CacheEntry(NamedTuple):
    data: Set[str]
    expires_at: float


class PermissoesCacheManager:
    """
    Gerenciador de Cache Híbrido para Permissões Funcionais do Usuário.
    Padrão de Chave: 'permissoes:{usuario_id}:{terminal_id}'
    """

    def __init__(self) -> None:
        self._memory_store: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._redis_client: Any = None
        self._initialized = False

    async def _get_redis(self) -> Any:
        """Inicializa conexão assíncrona com Redis se configurado no settings."""
        if not self._initialized:
            if settings.REDIS_URL:
                try:
                    import redis.asyncio as aioredis  # type: ignore
                    self._redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                except Exception:
                    self._redis_client = None
            self._initialized = True
        return self._redis_client

    async def get(self, key: str) -> Optional[Set[str]]:
        """
        Recupera conjunto de permissões do cache.
        Retorna None se houver cache-miss ou se a entrada expirou.
        """
        redis = await self._get_redis()
        if redis:
            try:
                members = await redis.smembers(key)
                if members:
                    return set(members)
                return None
            except Exception:
                # Fallback transparente para memória caso Redis falhe
                pass

        async with self._lock:
            entry = self._memory_store.get(key)
            if entry is None:
                return None
            if time.time() > entry.expires_at:
                del self._memory_store[key]
                return None
            return set(entry.data)

    async def set(self, key: str, value: Set[str], ttl_seconds: Optional[int] = None) -> None:
        """
        Armazena conjunto de permissões no cache com TTL determinado.
        """
        ttl = ttl_seconds if ttl_seconds is not None else settings.PERMISSOES_CACHE_TTL_SECONDS
        redis = await self._get_redis()
        if redis:
            try:
                async with redis.pipeline(transaction=True) as pipe:
                    await pipe.delete(key)
                    if value:
                        await pipe.sadd(key, *list(value))
                    else:
                        # Para representar conjunto vazio e evitar re-consulta imediata no banco
                        await pipe.sadd(key, "__VAZIO__")
                    await pipe.expire(key, ttl)
                    await pipe.execute()
                return
            except Exception:
                pass

        async with self._lock:
            expires_at = time.time() + ttl
            self._memory_store[key] = CacheEntry(data=set(value), expires_at=expires_at)

    async def delete(self, key: str) -> None:
        """Remove chave específica do cache (invalidação em tempo real)."""
        redis = await self._get_redis()
        if redis:
            try:
                await redis.delete(key)
            except Exception:
                pass

        async with self._lock:
            self._memory_store.pop(key, None)

    async def delete_pattern(self, pattern_prefix: str) -> None:
        """
        Invalida todas as chaves que iniciam com o prefixo informado.
        Exemplo: 'permissoes:42:' invalida todos os terminais do usuário 42.
        """
        redis = await self._get_redis()
        if redis:
            try:
                keys = await redis.keys(f"{pattern_prefix}*")
                if keys:
                    await redis.delete(*keys)
            except Exception:
                pass

        async with self._lock:
            keys_to_remove = [k for k in self._memory_store if k.startswith(pattern_prefix)]
            for k in keys_to_remove:
                self._memory_store.pop(k, None)

    async def clear(self) -> None:
        """Limpa todo o cache (utilizado primordialmente em suítes de teste)."""
        redis = await self._get_redis()
        if redis:
            try:
                await redis.flushdb()
            except Exception:
                pass

        async with self._lock:
            self._memory_store.clear()


# Instância Singleton do gerenciador de cache de permissões
permissoes_cache = PermissoesCacheManager()
