import io
import random

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.security import create_access_token
from app.domain.models import Usuario
from app.infra.database import AsyncSessionLocal

# PNG mínimo válido (assinatura + início do chunk IHDR).
FAKE_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"


def _digitos(prefixo: str, tamanho: int) -> str:
    base = (prefixo * tamanho)[:tamanho]
    return base.zfill(tamanho)


@pytest_asyncio.fixture
async def auth_headers() -> dict:
    """Cria um usuário ativo e retorna os headers de autenticação para o upload."""
    async with AsyncSessionLocal() as s:
        usuario = Usuario(
            nome="Uploader",
            sobrenome="Teste",
            cpf=_digitos(str(random.randint(1, 9)), 11),
            email=f"uploader_{random.randint(10**6, 10**7)}@teste.com",
            senha_hash="hash_teste",
            is_master=False,
            ativo=True,
            status_conta="ATIVO",
        )
        s.add(usuario)
        await s.commit()
        user_id = usuario.id

    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_upload_sem_autenticacao_bloqueado(client: AsyncClient):
    """Upload sem token deve ser rejeitado (401) — endpoint não é mais público."""
    files = {"arquivo": ("avatar.png", io.BytesIO(FAKE_PNG), "image/png")}
    response = await client.post("/api/v1/uploads/imagem?tipo=perfil", files=files)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_upload_foto_perfil_valida(client: AsyncClient, auth_headers: dict):
    """Testa upload de foto de perfil no storage dedicado (autenticado)."""
    files = {"arquivo": ("avatar.png", io.BytesIO(FAKE_PNG), "image/png")}
    response = await client.post(
        "/api/v1/uploads/imagem?tipo=perfil", files=files, headers=auth_headers
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "url" in data
    assert data["tipo"] == "perfil"
    assert data["url"].startswith("/api/v1/uploads/perfil/")

    # A leitura da imagem permanece pública (referenciada em <img src>).
    res_get = await client.get(data["url"])
    assert res_get.status_code == 200


@pytest.mark.asyncio
async def test_upload_congenere_formatos_permitidos(client: AsyncClient, auth_headers: dict):
    """Testa que congênere rejeita formatos inválidos e aceita PNG/JPG."""
    fake_gif = b"GIF89a"
    files_gif = {"arquivo": ("logo.gif", io.BytesIO(fake_gif), "image/gif")}
    res_fail = await client.post(
        "/api/v1/uploads/imagem?tipo=congenere", files=files_gif, headers=auth_headers
    )
    assert res_fail.status_code == 400
    assert "Formatos aceitos" in res_fail.json()["detail"]

    # Testa sucesso com PNG
    files_png = {"arquivo": ("logo.png", io.BytesIO(FAKE_PNG), "image/png")}
    res_ok = await client.post(
        "/api/v1/uploads/imagem?tipo=congenere", files=files_png, headers=auth_headers
    )
    assert res_ok.status_code == 201
    data = res_ok.json()
    assert data["tipo"] == "congenere"
    assert data["url"].startswith("/api/v1/uploads/congenere/")


@pytest.mark.asyncio
async def test_upload_conteudo_incompativel_rejeitado(client: AsyncClient, auth_headers: dict):
    """Arquivo com extensão .png mas conteúdo não-imagem deve ser rejeitado (magic bytes)."""
    fake = b"<html>not an image</html>"
    files = {"arquivo": ("fake.png", io.BytesIO(fake), "image/png")}
    res = await client.post(
        "/api/v1/uploads/imagem?tipo=perfil", files=files, headers=auth_headers
    )
    assert res.status_code == 400
