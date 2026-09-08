"""Roteador da API v1 para Gestão e Configuração do Terminal."""

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_db_session,
    obter_usuario_autenticado,
    resolver_terminal_ativo,
)
from app.domain.models import Usuario
from app.domain.schemas import TerminalDetalheDTO, TerminalGeralUpdateDTO
from app.services.terminal_service import terminal_service

router = APIRouter(prefix="/terminal", tags=["Gestão de Terminal"])


def _obter_terminal_id(request: Request, x_terminal_id: Optional[int]) -> int:
    terminal_id = resolver_terminal_ativo(request, x_terminal_id)
    if terminal_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de terminal não informado. Forneça o header 'X-Terminal-ID'.",
        )
    return terminal_id


@router.get(
    "",
    response_model=TerminalDetalheDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter Dados Completos do Terminal Ativo",
    description="Retorna as informações cadastrais, contatos e endereço do terminal ativo informado no header 'X-Terminal-ID'.",
)
async def obter_terminal(
    request: Request,
    _usuario: Usuario = Depends(obter_usuario_autenticado),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> TerminalDetalheDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await terminal_service.obter_terminal(session, terminal_id)


@router.put(
    "/geral",
    response_model=TerminalDetalheDTO,
    status_code=status.HTTP_200_OK,
    summary="Atualizar Informações Gerais do Terminal",
    description="Atualiza razão social, nome fantasia, cnpj, inscrição estadual, contatos e endereço do terminal ativo.",
)
async def atualizar_terminal_geral(
    request: Request,
    payload: TerminalGeralUpdateDTO,
    _usuario: Usuario = Depends(obter_usuario_autenticado),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> TerminalDetalheDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await terminal_service.atualizar_geral(session, terminal_id, payload)
