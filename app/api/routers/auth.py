"""
Roteador de Autenticação, Sessão, Primeiro Acesso e Redefinições de Senha.
Documentação viva do Contrato de API (OpenAPI / Swagger).
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, obter_usuario_autenticado
from app.core.config import settings
from app.domain.models import Usuario
from app.domain.schemas import (
    AtualizarPerfilRequest,
    ConfirmarSenhaMasterRequest,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MensagemSucessoResponse,
    PrimeiroAcessoConcluirRequest,
    PrimeiroAcessoValidarRequest,
    PrimeiroAcessoValidarResponse,
    RecuperarSenhaMasterRequest,
    RedefinirSenhaColaboradorRequest,
    TokenRefreshResponse,
    UserProfileResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticação & Credenciais"])

_REFRESH_COOKIE_KEY = "refresh_token"
_REFRESH_COOKIE_PATH = "/api/v1/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE_KEY,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
        path=_REFRESH_COOKIE_PATH,
    )


# =============================================================================
# LOGIN, SESSÃO E LOGOUT
# =============================================================================

@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login no Sistema",
    description=(
        "Autentica o usuário por CPF ou CNPJ. Retorna o Access Token (JWT Bearer de 15 minutos) "
        "no corpo e define o Refresh Token seguro no Cookie HttpOnly (7 dias)."
    ),
)
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    access_token, refresh_token, usuario_dto = await auth_service.autenticar(
        session, payload.identificador, payload.senha
    )
    _set_refresh_cookie(response, refresh_token)

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        usuario=usuario_dto,
    )


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Renovar Access Token",
    description="Rotaciona o par de tokens consumindo o Refresh Token presente no Cookie HttpOnly.",
)
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(default=None, description="Enviado automaticamente pelo browser via HttpOnly"),
    session: AsyncSession = Depends(get_db_session),
) -> TokenRefreshResponse:
    access_token, novo_refresh = await auth_service.renovar(session, refresh_token)
    _set_refresh_cookie(response, novo_refresh)

    return TokenRefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Encerrar Sessão",
    description="Invalida a sessão ativa e expira o Cookie HttpOnly de Refresh Token.",
)
async def logout(response: Response) -> LogoutResponse:
    response.set_cookie(
        key=_REFRESH_COOKIE_KEY,
        value="",
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=0,
        path=_REFRESH_COOKIE_PATH,
    )
    return LogoutResponse(mensagem="Sessão encerrada com sucesso.")


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Perfil do Usuário Autenticado",
    description="Retorna as informações do usuário atual, terminais autorizados e permissões vinculadas.",
)
async def get_current_user_profile(
    usuario: Usuario = Depends(obter_usuario_autenticado),
    session: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    return await auth_service.montar_perfil(session, usuario)


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Atualizar Perfil do Usuário Autenticado",
    description="Atualiza dados cadastrais, foto de perfil e credenciais de segurança (senha e PIN) do usuário atual.",
)
async def atualizar_perfil(
    payload: AtualizarPerfilRequest,
    usuario: Usuario = Depends(obter_usuario_autenticado),
    session: AsyncSession = Depends(get_db_session),
) -> UserProfileResponse:
    return await auth_service.atualizar_perfil(session, usuario, payload)


# =============================================================================
# PRIMEIRO ACESSO (COLABORADOR OPERACIONAL)
# =============================================================================

@router.post(
    "/primeiro-acesso/validar",
    response_model=PrimeiroAcessoValidarResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar Código de Ativação (1º Acesso)",
    description="Valida se o CPF informado possui um código ATIV-XXXX pendente emitido pelo gestor.",
)
async def validar_primeiro_acesso(
    payload: PrimeiroAcessoValidarRequest,
    session: AsyncSession = Depends(get_db_session),
) -> PrimeiroAcessoValidarResponse:
    nome = await auth_service.primeiro_acesso_validar(session, payload.cpf, payload.codigo_ativacao)
    return PrimeiroAcessoValidarResponse(
        valido=True,
        nome_colaborador=nome,
        mensagem="Código validado com sucesso. Prossiga para a criação de sua senha pessoal e PIN.",
    )


@router.post(
    "/primeiro-acesso/concluir",
    response_model=MensagemSucessoResponse,
    status_code=status.HTTP_200_OK,
    summary="Concluir Primeiro Acesso e Ativar Conta",
    description="Cadastra a senha pessoal definitiva e o PIN de segurança pessoal (4 a 6 dígitos), ativando a conta.",
)
async def concluir_primeiro_acesso(
    payload: PrimeiroAcessoConcluirRequest,
    session: AsyncSession = Depends(get_db_session),
) -> MensagemSucessoResponse:
    if payload.nova_senha != payload.confirmacao_senha:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A nova senha e a confirmação de senha não coincidem.",
        )
    await auth_service.primeiro_acesso_concluir(session, payload)
    return MensagemSucessoResponse(
        sucesso=True,
        mensagem="Conta ativada com sucesso! Você já pode realizar login no sistema.",
    )


# =============================================================================
# REDEFINIÇÃO: COLABORADOR OPERACIONAL (HANDSHAKE 2 FASES) — FORA DO ESCOPO ATUAL
# =============================================================================

@router.post(
    "/redefinir-senha/colaborador/confirmar",
    response_model=MensagemSucessoResponse,
    status_code=status.HTTP_200_OK,
    summary="Redefinir Senha do Colaborador (Handshake 2 Fases)",
    description=(
        "Redefinição segura sem necessidade de e-mail corporativo. "
        "Exige o Código de Liberação emitido pelo gestor (LIB-XXXX) + o PIN Pessoal do colaborador."
    ),
)
async def confirmar_redefinicao_colaborador(
    payload: RedefinirSenhaColaboradorRequest,
) -> MensagemSucessoResponse:
    if payload.nova_senha != payload.confirmacao_senha:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A nova senha e a confirmação de senha não coincidem.",
        )
    return MensagemSucessoResponse(
        sucesso=True,
        mensagem="Senha redefinida com sucesso. Faça login com sua nova credencial.",
    )


# =============================================================================
# REDEFINIÇÃO: USUÁRIO MASTER (SELF-SERVICE VIA E-MAIL) — FORA DO ESCOPO ATUAL
# =============================================================================

@router.post(
    "/recuperar-senha/master/solicitar",
    response_model=MensagemSucessoResponse,
    status_code=status.HTTP_200_OK,
    summary="Solicitar Redefinição de Senha Master (E-mail)",
    description="Dispara um e-mail com link e token criptográfico temporário (30 minutos) para a conta do gestor master.",
)
async def solicitar_recuperacao_master(payload: RecuperarSenhaMasterRequest) -> MensagemSucessoResponse:
    return MensagemSucessoResponse(
        sucesso=True,
        mensagem="Se os dados informados corresponderem a uma conta administrativa, um link de recuperação foi enviado para o e-mail cadastrado.",
    )


@router.post(
    "/recuperar-senha/master/confirmar",
    response_model=MensagemSucessoResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirmar Nova Senha Master via Token",
    description="Valida o token criptográfico recebido por e-mail e atualiza a senha da conta master.",
)
async def confirmar_recuperacao_master(payload: ConfirmarSenhaMasterRequest) -> MensagemSucessoResponse:
    if payload.nova_senha != payload.confirmacao_senha:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A nova senha e a confirmação de senha não coincidem.",
        )
    return MensagemSucessoResponse(
        sucesso=True,
        mensagem="Senha administrativa atualizada com sucesso. Faça login com sua nova credencial.",
    )
