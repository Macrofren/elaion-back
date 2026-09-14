from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valores conhecidos que NUNCA podem ser aceitos em produção (fail-fast).
_JWT_SECRETS_INSEGUROS = {
    "",
    "elaion_jwt_secret_dev_key_2026_super_secure",
    "changeme",
    "change-me",
    "secret",
    "dev",
}


class Settings(BaseSettings):
    """Configurações globais da aplicação lidas do arquivo .env via Pydantic Settings."""
    PROJECT_NAME: str = "Elaion API - Gestão de Terminais"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "elaion_db"

    # Obrigatório (sem default): a aplicação NÃO sobe sem uma URL de banco explícita.
    DATABASE_URL: str

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # JWT & Autenticação
    # Obrigatório e sem default: força o operador a definir uma chave forte no ambiente.
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias

    # Política unificada de credenciais (senha e PIN)
    SENHA_MIN_LENGTH: int = 8
    PIN_LENGTH: int = 4

    # Rate limiting de endpoints sensíveis (janela em segundos)
    RATE_LIMIT_LOGIN_MAX: int = 10
    RATE_LIMIT_LOGIN_WINDOW: int = 60
    RATE_LIMIT_CODIGO_MAX: int = 8
    RATE_LIMIT_CODIGO_WINDOW: int = 60

    # Códigos operacionais (Primeiro Acesso / Redefinição Presencial)
    CODIGO_ATIVACAO_PREFIX: str = "ATIV"
    CODIGO_LIBERACAO_PREFIX: str = "LIB"
    LIB_CODIGO_EXPIRE_MINUTES: int = 15

    # Cache RBAC (Opção 2)
    PERMISSOES_CACHE_TTL_SECONDS: int = 900
    REDIS_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _validar_jwt_secret(cls, valor: str) -> str:
        """Impede a inicialização com uma chave JWT ausente, padrão ou fraca."""
        if valor.strip().lower() in _JWT_SECRETS_INSEGUROS:
            raise ValueError(
                "JWT_SECRET_KEY inválida ou padrão de desenvolvimento. "
                "Defina uma chave forte e única na variável de ambiente JWT_SECRET_KEY "
                "(ex.: `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`)."
            )
        if len(valor) < 32:
            raise ValueError("JWT_SECRET_KEY muito curta: utilize no mínimo 32 caracteres aleatórios.")
        return valor


settings = Settings()
