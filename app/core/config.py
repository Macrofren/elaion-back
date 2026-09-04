from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações globais da aplicação lidas do arquivo .env via Pydantic Settings."""
    PROJECT_NAME: str = "Elaion API - Gestão de Terminais"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "elaion_db"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/elaion_db"

    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # JWT & Autenticação
    JWT_SECRET_KEY: str = "elaion_jwt_secret_dev_key_2026_super_secure"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 dias

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


settings = Settings()
