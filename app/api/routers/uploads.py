"""
Roteador de Uploads e Armazenamento de Imagens (Storage Dedicado).
Permite upload e visualização de fotos de perfil e logos de congêneres.
"""

import os
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

router = APIRouter(prefix="/uploads", tags=["Uploads & Storage"])

# Diretório base de armazenamento
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # backend/
STORAGE_DIR = BASE_DIR / "storage" / "uploads"
STORAGE_PERFIL = STORAGE_DIR / "fotos_perfil"
STORAGE_CONGENERE = STORAGE_DIR / "logos_congeneres"

# Garante a existência dos diretórios de storage
STORAGE_PERFIL.mkdir(parents=True, exist_ok=True)
STORAGE_CONGENERE.mkdir(parents=True, exist_ok=True)

EXTENSOES_PERFIL = {".png", ".jpg", ".jpeg", ".webp"}
MIMES_PERFIL = {"image/png", "image/jpeg", "image/webp"}


@router.post("/imagem", status_code=status.HTTP_201_CREATED)
async def upload_imagem(
    tipo: Literal["perfil", "congenere"] = Query(
        ..., description="Tipo da imagem: 'perfil' ou 'congenere'"
    ),
    arquivo: UploadFile = File(..., description="Arquivo de imagem a ser enviado"),
):
    """
    Realiza o upload de imagem para o storage dedicado.
    - Para 'congenere': aceita EXCLUSIVAMENTE arquivos PNG (.png).
    - Para 'perfil': aceita PNG, JPG, JPEG ou WEBP.
    """
    nome_original = arquivo.filename or "imagem"
    extensao = os.path.splitext(nome_original)[1].lower()
    content_type = (arquivo.content_type or "").lower()

    if tipo == "congenere":
        if extensao != ".png" or (content_type and content_type != "image/png"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Para logo de congêneres, apenas arquivos PNG são permitidos.",
            )
        target_dir = STORAGE_CONGENERE
    else:
        if extensao not in EXTENSOES_PERFIL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de imagem inválido para foto de perfil. Formatos aceitos: PNG, JPG ou WEBP.",
            )
        target_dir = STORAGE_PERFIL

    # Nome único seguro
    novo_nome = f"{uuid.uuid4().hex}{extensao}"
    destino = target_dir / novo_nome

    try:
        conteudo = await arquivo.read()
        # Limite máximo de 5MB
        if len(conteudo) > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="O arquivo excede o tamanho máximo permitido de 5MB.",
            )

        with open(destino, "wb") as f:
            f.write(conteudo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar arquivo no storage: {str(e)}",
        )

    url_publica = f"/api/v1/uploads/{tipo}/{novo_nome}"
    return {
        "url": url_publica,
        "filename": novo_nome,
        "tipo": tipo,
        "content_type": content_type or f"image/{extensao.replace('.', '')}",
    }


@router.get("/{tipo}/{filename}")
async def obter_imagem(
    tipo: Literal["perfil", "congenere"],
    filename: str,
):
    """Serve uma imagem armazenada no storage dedicado."""
    # Prevenção contra path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de arquivo inválido.",
        )

    target_dir = STORAGE_CONGENERE if tipo == "congenere" else STORAGE_PERFIL
    arquivo_path = target_dir / filename

    if not arquivo_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagem não encontrada no storage.",
        )

    ext = arquivo_path.suffix.lower()
    media_type = "image/png" if ext == ".png" else "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/webp"
    return FileResponse(arquivo_path, media_type=media_type)
