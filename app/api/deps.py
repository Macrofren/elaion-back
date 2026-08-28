from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.infra.database import AsyncSessionLocal


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Gerador de dependência da Sessão Assíncrona do Banco de Dados.
    Utilizado nas rotas HTTP via Depends(get_db_session).
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
