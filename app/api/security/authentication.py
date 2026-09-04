"""
Autenticação (AuthN) da camada de API.

Dependência responsável por validar o Bearer Token JWT e carregar o usuário
autenticado a partir do banco de dados relacional.
"""

from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.domain.models import Usuario
from app.infra.database import AsyncSessionLocal


async def get_db_session():
    """
    Gerador de dependência da Sessão Assíncrona do Banco de Dados.
    Mantido aqui para evitar import circular com app.api.deps.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def obter_usuario_autenticado(
    authorization: Optional[str] = Header(None, description="Bearer <access_token>"),
    session: AsyncSession = Depends(get_db_session),
) -> Usuario:
    """
    Valida rigorosamente o Bearer Token JWT via PyJWT e carrega o Usuário autenticado
    do banco de dados.
    Lança HTTP 401 se ausente, inválido, expirado ou se o usuário não existir.
    Lança HTTP 403 se o usuário estiver inativo ou pendente de ativação.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido ou formato inválido.",
        )

    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado. Por favor, renove sua sessão.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou assinatura incorreta.",
        )

    user_id_raw = payload.get("sub")
    if not user_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificador de usuário (sub).",
        )

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identificador de usuário inválido no token.",
        )

    stmt = select(Usuario).where(Usuario.id == user_id)
    result = await session.execute(stmt)
    usuario = result.scalar_one_or_none()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário do token não encontrado.",
        )

    if not usuario.ativo or usuario.status_conta != "ATIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta de usuário inativa ou pendente de ativação.",
        )

    return usuario
