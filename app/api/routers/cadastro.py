"""
Roteador de Cadastro e Onboarding do Terminal (Assinatura Comercial).
Totalmente compatível com o wizard de 4 steps do Frontend (/cadastro).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.domain.schemas import (
    RegistrationPayload,
    RegistrationResponse,
    ValidarCodigoAssinaturaRequest,
    ValidarCodigoAssinaturaResponse,
)
from app.services import cadastro_service

router = APIRouter(prefix="/cadastro", tags=["Cadastro & Onboarding de Terminal"])


@router.post(
    "/validar-codigo",
    response_model=ValidarCodigoAssinaturaResponse,
    status_code=status.HTTP_200_OK,
    summary="Validar Código de Assinatura (Step 1 do Onboarding)",
    description=(
        "Valida se o código comercial ELAION-XXXX-XXXX emitido pelo SaaS é legítimo e ainda não foi utilizado. "
        "Consumido pelo Step 1 da tela de cadastro (/cadastro)."
    ),
)
async def validar_codigo_assinatura(
    payload: ValidarCodigoAssinaturaRequest,
    session: AsyncSession = Depends(get_db_session),
) -> ValidarCodigoAssinaturaResponse:
    await cadastro_service.validar_codigo(session, payload.codigo)
    return ValidarCodigoAssinaturaResponse(valid=True, message="Código de ativação válido.")


@router.post(
    "/registrar",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar Organização, Terminal e Master (Step 4 do Onboarding)",
    description=(
        "Conclui o onboarding após o preenchimento dos dados da Organização, Terminal e Senha do Master, "
        "consumindo o código de assinatura na tabela convite_cadastro."
    ),
)
async def registrar_organizacao_terminal(
    payload: RegistrationPayload,
    session: AsyncSession = Depends(get_db_session),
) -> RegistrationResponse:
    organizacao = await cadastro_service.registrar(session, payload)
    return RegistrationResponse(id=organizacao.id, message="Cadastro realizado com sucesso.")
