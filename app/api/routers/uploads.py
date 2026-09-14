"""
Roteador de Uploads e Armazenamento de Imagens (Storage Dedicado).
Permite upload e visualização de fotos de perfil e logos de congêneres.
"""

import os
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.api.deps import obter_usuario_autenticado
from app.domain.models import Usuario

router = APIRouter(prefix="/uploads", tags=["Uploads & Storage"])

# Limite máximo do arquivo (bytes).
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024


def _detectar_mime(conteudo: bytes) -> str | None:
    """Detecta o tipo de imagem pelos bytes iniciais (magic bytes)."""
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "image/webp"
    return None

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
    _usuario: Usuario = Depends(obter_usuario_autenticado),
):
    """
    Realiza o upload de imagem para o storage dedicado (requer autenticação).
    - Para 'congenere' e 'perfil': aceita PNG, JPG, JPEG ou WEBP.
    """
    nome_original = arquivo.filename or "imagem"
    extensao = os.path.splitext(nome_original)[1].lower()
    content_type = (arquivo.content_type or "").lower()

    if extensao not in EXTENSOES_PERFIL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de imagem inválido. Formatos aceitos: PNG, JPG, JPEG ou WEBP.",
        )
    if content_type not in MIMES_PERFIL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content-Type inválido. Formatos aceitos: image/png, image/jpeg ou image/webp.",
        )

    target_dir = STORAGE_CONGENERE if tipo == "congenere" else STORAGE_PERFIL

    # Leitura com guarda de tamanho por streaming (evita esgotar a RAM).
    conteudo = bytearray()
    while True:
        pedaco = await arquivo.read(64 * 1024)
        if not pedaco:
            break
        conteudo.extend(pedaco)
        if len(conteudo) > TAMANHO_MAXIMO_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="O arquivo excede o tamanho máximo permitido de 5MB.",
            )

    # Valida o conteúdo real por magic bytes (impede arquivos disfarçados de imagem).
    mime_real = _detectar_mime(bytes(conteudo[:16]))
    if mime_real is None or mime_real not in MIMES_PERFIL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O conteúdo enviado não corresponde a uma imagem PNG, JPEG ou WEBP válida.",
        )

    novo_nome = f"{uuid.uuid4().hex}{extensao}"
    destino = target_dir / novo_nome
    try:
        with open(destino, "wb") as f:
            f.write(conteudo)
    except OSError:
        # Não vaza detalhes internos do sistema de arquivos ao cliente.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar o arquivo no storage.",
        )

    url_publica = f"/api/v1/uploads/{tipo}/{novo_nome}"
    return {
        "url": url_publica,
        "filename": novo_nome,
        "tipo": tipo,
        "content_type": mime_real,
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
