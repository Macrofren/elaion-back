"""
Roteador de Gestão de Usuários e Colaboradores do Terminal.
Permite ao Gestor Master criar operadores, listar equipe e autorizar redefinições presenciais.
"""

from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import exige_permissao, get_db_session
from app.domain.models import Usuario
from app.domain.schemas import (
    AutorizarRedefinicaoResponse,
    CatalogoPermissoesModuloDTO,
    CriarUsuarioTerminalRequest,
    CriarUsuarioTerminalResponse,
    UsuarioTerminalResumoDTO,
)
from app.services import usuarios_service

router = APIRouter(prefix="/terminais/{terminal_id}/usuarios", tags=["Gestão de Usuários do Terminal"])


@router.get(
    "/permissoes-disponiveis",
    response_model=List[CatalogoPermissoesModuloDTO],
    status_code=status.HTTP_200_OK,
    summary="Catálogo de Permissões Disponíveis (Alimenta os Seletores do Drawer)",
    description=(
        "Retorna a árvore de permissões e funcionalidades dos módulos contratados pelo terminal (ex: SIRAC). "
        "Consumido pelo Drawer de Novo Colaborador para exibir as caixas de seleção com seus respectivos IDs e chaves."
    ),
)
async def obter_permissoes_disponiveis(
    terminal_id: int,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:usuarios:visualizar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: int = Header(..., alias="X-Terminal-ID"),
) -> List[CatalogoPermissoesModuloDTO]:
    return await usuarios_service.catalogo_permissoes(session, terminal_id)


@router.post(
    "",
    response_model=CriarUsuarioTerminalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar Colaborador no Terminal (Gera ATIV-XXXX)",
    description=(
        "Exclusivo para Gestores Master. Cria o colaborador vinculado ao terminal com seu Papel "
        "(Porteiro, Químico, Operador, Adm ou Congênere), atribui as permissões do SIRAC e emite o código ATIV-XXXX."
    ),
)
async def criar_usuario_terminal(
    terminal_id: int,
    payload: CriarUsuarioTerminalRequest,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:usuarios:registrar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: int = Header(..., alias="X-Terminal-ID", description="ID do terminal em operação"),
) -> CriarUsuarioTerminalResponse:
    if terminal_id != x_terminal_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O terminal da rota diverge do terminal ativo no header X-Terminal-ID.",
        )
    return await usuarios_service.criar_colaborador(session, terminal_id, payload)


@router.get(
    "",
    response_model=List[UsuarioTerminalResumoDTO],
    status_code=status.HTTP_200_OK,
    summary="Listar Colaboradores do Terminal",
    description="Retorna a lista de colaboradores associados ao terminal especificado.",
)
async def listar_usuarios_terminal(
    terminal_id: int,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:usuarios:visualizar")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: int = Header(..., alias="X-Terminal-ID"),
) -> List[UsuarioTerminalResumoDTO]:
    return await usuarios_service.listar_colaboradores(session, terminal_id)


@router.post(
    "/{usuario_id}/autorizar-redefinicao",
    response_model=AutorizarRedefinicaoResponse,
    status_code=status.HTTP_200_OK,
    summary="Autorizar Redefinição de Senha (Gera LIB-XXXX)",
    description=(
        "Fase 1 do Handshake Zero-Trust. O Gestor Master valida a identidade presencial do colaborador "
        "e autoriza a emissão de um código temporário de liberação (LIB-XXXX) válido por 15 minutos."
    ),
)
async def autorizar_redefinicao_senha(
    terminal_id: int,
    usuario_id: int,
    _usuario: Usuario = Depends(exige_permissao("sirac:config:usuarios:detalhes")),
    session: AsyncSession = Depends(get_db_session),
    x_terminal_id: int = Header(..., alias="X-Terminal-ID"),
) -> AutorizarRedefinicaoResponse:
    return await usuarios_service.autorizar_redefinicao(session, terminal_id, usuario_id)
