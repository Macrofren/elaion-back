from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.api.exceptions import setup_exception_handlers
from app.api.routers.api_v1 import api_router
from app.core.config import settings
from app.core.security import setup_cors
from app.infra.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Executa verificações de schema e inicializações no startup da API."""
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE bico ADD COLUMN IF NOT EXISTS tipo_operacao VARCHAR(30) NOT NULL DEFAULT 'CARREGAMENTO';"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE bico ALTER COLUMN produto DROP NOT NULL;"
            )
        )
        await conn.execute(
            text(
                "UPDATE alembic_version SET version_num = 'b2c3d4e5f6a7' WHERE version_num = 'a1b2c3d4e5f6';"
            )
        )
    yield


def create_application() -> FastAPI:
    """Factory principal de inicialização da API Elaion."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API RESTful do Elaion baseada em FastAPI, SQLAlchemy 2.0 (Async) e Clean Architecture.",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # 1. Configurar Middleware CORS
    setup_cors(app)

    # 2. Configurar Handlers Globais de Exceção
    setup_exception_handlers(app)

    # 3. Incluir Roteador Principal v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()

