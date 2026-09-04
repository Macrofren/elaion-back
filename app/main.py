from fastapi import FastAPI
from app.api.exceptions import setup_exception_handlers
from app.api.routers.api_v1 import api_router
from app.core.config import settings
from app.core.security import setup_cors


def create_application() -> FastAPI:
    """Factory principal de inicialização da API Elaion."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API RESTful do Elaion baseada em FastAPI, SQLAlchemy 2.0 (Async) e Clean Architecture.",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
    )

    # 1. Configurar Middleware CORS
    setup_cors(app)

    # 2. Configurar Handlers Globais de Exceção
    setup_exception_handlers(app)

    # 3. Incluir Roteador Principal v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
