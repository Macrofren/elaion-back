from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.infra.database import AsyncSessionLocal, engine
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine() -> AsyncGenerator[None, None]:
    """
    Descarta o pool de conexões ao fim de cada teste. Como o pytest-asyncio usa um
    event loop por teste, isso evita reutilizar conexões asyncpg criadas em um loop
    já encerrado ("Event loop is closed").
    """
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture que fornece uma sessão assíncrona com o PostgreSQL."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Fixture de cliente HTTP assíncrono (httpx.AsyncClient) com sobrescrita da sessão do BD."""
    async def override_get_db_session():
        yield db_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
