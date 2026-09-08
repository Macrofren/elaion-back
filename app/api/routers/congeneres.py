"""Roteador da API v1 para Gestão de Congêneres do Terminal."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import exige_permissao, get_db_session, resolver_terminal_ativo
from app.domain.models import Usuario
from app.domain.schemas import CongenereCreateDTO, CongenereResponseDTO, CongenereUpdateDTO
from app.services.congeneres_service import congeneres_service

router = APIRouter(prefix="/congeneres", tags=["Gestão de Congêneres"])


def _obter_terminal_id(request: Request, x_terminal_id: Optional[int]) -> int:
    terminal_id = resolver_terminal_ativo(request, x_terminal_id)
    if terminal_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de terminal não informado. Forneça o header 'X-Terminal-ID'.",
        )
    return terminal_id


@router.post(
    "",
    response_model=CongenereResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Congênere no Terminal",
    description=(
        "Cadastra uma nova distribuidora congênere vinculada ao terminal ativo do usuário. "
        "Requer permissão 'sirac:config:congenere:registrar' ou usuário Master."
    ),
)
async def cadastrar_congenere(
    request: Request,
    payload: CongenereCreateDTO,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:congenere:registrar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> CongenereResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await congeneres_service.cadastrar_congenere(session, terminal_id, payload)


@router.get(
    "",
    response_model=List[CongenereResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Congêneres do Terminal",
    description=(
        "Retorna a lista de congêneres cadastradas no terminal ativo. "
        "Requer permissão 'sirac:config:congenere:visualizar' ou usuário Master."
    ),
)
async def listar_congeneres(
    request: Request,
    busca: Optional[str] = Query(None, description="Filtro textual livre por razão social, cnpj, email etc."),
    _usuario: Usuario = Depends(exige_permissao("sirac:config:congenere:visualizar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> List[CongenereResponseDTO]:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await congeneres_service.listar_congeneres(session, terminal_id, busca)


@router.get(
    "/{congenere_id}",
    response_model=CongenereResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Obter Detalhes da Congênere",
    description="Retorna os dados cadastrais da congênere pelo seu ID.",
)
async def obter_congenere_por_id(
    request: Request,
    congenere_id: int,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:congenere:visualizar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> CongenereResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await congeneres_service.obter_congenere_por_id(session, terminal_id, congenere_id)


@router.put(
    "/{congenere_id}",
    response_model=CongenereResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Atualizar Dados da Congênere",
    description="Atualiza as informações de uma congênere. Requer permissão 'sirac:config:congenere:editar'.",
)
async def atualizar_congenere(
    request: Request,
    congenere_id: int,
    payload: CongenereUpdateDTO,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:congenere:editar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: Optional[int] = Header(None, alias="X-Terminal-ID"),
) -> CongenereResponseDTO:
    terminal_id = _obter_terminal_id(request, x_terminal_id)
    return await congeneres_service.atualizar_congenere(session, terminal_id, congenere_id, payload)
