from fastapi import APIRouter
from app.api.routers.auth import router as auth_router
from app.api.routers.cadastro import router as cadastro_router
from app.api.routers.usuarios import router as usuarios_router
from app.api.routers.uploads import router as uploads_router

api_router = APIRouter()

@api_router.get("/health", tags=["Health"])
async def health_check():
    """Endpoint básico de health check da API v1."""
    return {"status": "ok", "service": "elaion-backend"}

# Inclusão dos Roteadores da API v1
api_router.include_router(cadastro_router)
api_router.include_router(auth_router)
api_router.include_router(usuarios_router)
api_router.include_router(uploads_router)


