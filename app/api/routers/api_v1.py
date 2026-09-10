from fastapi import APIRouter
from app.api.routers.auth import router as auth_router
from app.api.routers.cadastro import router as cadastro_router
from app.api.routers.usuarios import router as usuarios_router
from app.api.routers.congeneres import router as congeneres_router
from app.api.routers.uploads import router as uploads_router
from app.api.routers.terminais import router as terminais_router
from app.api.routers.laboratorios import router as laboratorios_router
from app.api.routers.plataformas import router as plataformas_router
from app.api.routers.tanques import router as tanques_router
from app.api.routers.bicos import router as bicos_router
from app.api.routers.operacao import router as operacao_router

api_router = APIRouter()

@api_router.get("/health", tags=["Health"])
async def health_check():
    """Endpoint básico de health check da API v1."""
    return {"status": "ok", "service": "elaion-backend"}

# Inclusão dos Roteadores da API v1
api_router.include_router(cadastro_router)
api_router.include_router(auth_router)
api_router.include_router(usuarios_router)
api_router.include_router(congeneres_router)
api_router.include_router(terminais_router)
api_router.include_router(laboratorios_router)
api_router.include_router(plataformas_router)
api_router.include_router(tanques_router)
api_router.include_router(bicos_router)
api_router.include_router(uploads_router)
api_router.include_router(operacao_router)



