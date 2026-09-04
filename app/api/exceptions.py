from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Exceções de domínio puras (definidas fora da camada web).
from app.domain.exceptions import (  # noqa: F401  (re-export por compatibilidade)
    AcessoNegadoException,
    ConflitoException,
    DomainException,
    ItemNaoEncontradoException,
    NaoAutorizadoException,
    RegraNegocioException,
)


# Alias mantido por compatibilidade com código/testes existentes.
class ItemNotFoundException(ItemNaoEncontradoException):
    def __init__(self, item_id: str):
        super().__init__(f"Item com ID '{item_id}' não foi encontrado.")


def setup_exception_handlers(app: FastAPI) -> None:
    """Registra handlers globais para capturar exceções de domínio."""

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
