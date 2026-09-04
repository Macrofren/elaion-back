"""
Exceções de domínio (puras, sem dependência de bibliotecas web).

Levantadas pela camada de Services (regras de negócio) e traduzidas em respostas
HTTP pelo handler global registrado em app/api/exceptions.py.
"""


class DomainException(Exception):
    """Exceção base para regras de negócio da camada Service."""

    status_code: int = 400

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(message)


class RegraNegocioException(DomainException):
    """Violação de regra de negócio (HTTP 400)."""

    status_code = 400


class NaoAutorizadoException(DomainException):
    """Credenciais inválidas ou não autenticado (HTTP 401)."""

    status_code = 401


class AcessoNegadoException(DomainException):
    """Usuário autenticado sem permissão para a ação (HTTP 403)."""

    status_code = 403


class ItemNaoEncontradoException(DomainException):
    """Recurso inexistente (HTTP 404)."""

    status_code = 404

    def __init__(self, message: str = "Recurso não encontrado."):
        super().__init__(message, status_code=404)


class ConflitoException(DomainException):
    """Conflito de estado, ex: registro duplicado (HTTP 409)."""

    status_code = 409
