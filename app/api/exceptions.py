from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class DomainException(Exception):
    """Exceção base para regras de negócio da camada Service."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ItemNotFoundException(DomainException):
    def __init__(self, item_id: str):
        super().__init__(
            message=f"Item com ID '{item_id}' não foi encontrado.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


def setup_exception_handlers(app: FastAPI) -> None:
    """Registra handlers globais para capturar exceções de domínio."""
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
