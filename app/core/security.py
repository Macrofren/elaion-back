from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from passlib.context import CryptContext
from app.core.config import settings


# Contexto de hashing (bcrypt) reutilizado para senhas e PINs de segurança.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def setup_cors(app: FastAPI) -> None:
    """Configura o middleware de CORS na aplicação FastAPI."""
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Gera um JWT assinado com HMAC-SHA256 (HS256).
    O payload deve conter ao menos: 'sub' (id do usuário como string) e claims leves.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decodifica e valida a assinatura e expiração de um token JWT.
    Lança jwt.ExpiredSignatureError se expirado ou jwt.PyJWTError se inválido.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# =============================================================================
# HASHING DE SENHAS E PINS (bcrypt via passlib)
# =============================================================================

def hash_password(senha: str) -> str:
    """Gera o hash bcrypt de uma senha em texto plano."""
    return pwd_context.hash(senha)


def verify_password(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash armazenado."""
    try:
        return pwd_context.verify(senha, senha_hash)
    except (ValueError, TypeError):
        return False


def hash_pin(pin: str) -> str:
    """Gera o hash bcrypt do PIN de segurança pessoal."""
    return pwd_context.hash(pin)


def verify_pin(pin: str, pin_hash: str) -> bool:
    """Verifica se o PIN em texto plano corresponde ao hash armazenado."""
    try:
        return pwd_context.verify(pin, pin_hash)
    except (ValueError, TypeError):
        return False


# =============================================================================
# REFRESH TOKEN (JWT stateless assinado, claim type=refresh)
# =============================================================================

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Gera um Refresh Token JWT assinado (claim 'type'='refresh') de longa duração.
    Utilizado exclusivamente no Cookie HttpOnly para rotacionar o Access Token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_refresh_token(token: str) -> dict:
    """
    Decodifica e valida um Refresh Token JWT.
    Lança jwt.ExpiredSignatureError se expirado ou jwt.PyJWTError se inválido
    (inclusive se o claim 'type' não for 'refresh').
    """
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Token não é um refresh token válido.")
    return payload
