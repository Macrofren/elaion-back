import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_foto_perfil_valida(client: AsyncClient):
    """Testa upload de foto de perfil no storage dedicado."""
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    files = {"arquivo": ("avatar.png", io.BytesIO(fake_png), "image/png")}
    response = await client.post("/api/v1/uploads/imagem?tipo=perfil", files=files)
    assert response.status_code == 201
    data = response.json()
    assert "url" in data
    assert data["tipo"] == "perfil"
    assert data["url"].startswith("/api/v1/uploads/perfil/")

    # Testa busca da imagem
    res_get = await client.get(data["url"])
    assert res_get.status_code == 200


@pytest.mark.asyncio
async def test_upload_congenere_formatos_permitidos(client: AsyncClient):
    """Testa que congênere rejeita formatos inválidos e aceita PNG/JPG."""
    fake_gif = b"GIF89a"
    files_gif = {"arquivo": ("logo.gif", io.BytesIO(fake_gif), "image/gif")}
    res_fail = await client.post("/api/v1/uploads/imagem?tipo=congenere", files=files_gif)
    assert res_fail.status_code == 400
    assert "Formatos aceitos" in res_fail.json()["detail"]

    # Testa sucesso com PNG
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    files_png = {"arquivo": ("logo.png", io.BytesIO(fake_png), "image/png")}
    res_ok = await client.post("/api/v1/uploads/imagem?tipo=congenere", files=files_png)
    assert res_ok.status_code == 201
    data = res_ok.json()
    assert data["tipo"] == "congenere"
    assert data["url"].startswith("/api/v1/uploads/congenere/")

