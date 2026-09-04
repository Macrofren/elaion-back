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
async def test_upload_congenere_png_obrigatorio(client: AsyncClient):
    """Testa que congênere aceita somente PNG e rejeita outros formatos."""
    fake_jpg = b"\xff\xd8\xff\xe0\x00\x10JFIF"
    files_jpg = {"arquivo": ("logo.jpg", io.BytesIO(fake_jpg), "image/jpeg")}
    res_fail = await client.post("/api/v1/uploads/imagem?tipo=congenere", files=files_jpg)
    assert res_fail.status_code == 400
    assert "apenas arquivos PNG são permitidos" in res_fail.json()["detail"]

    # Testa sucesso com PNG
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    files_png = {"arquivo": ("logo.png", io.BytesIO(fake_png), "image/png")}
    res_ok = await client.post("/api/v1/uploads/imagem?tipo=congenere", files=files_png)
    assert res_ok.status_code == 201
    data = res_ok.json()
    assert data["tipo"] == "congenere"
    assert data["url"].startswith("/api/v1/uploads/congenere/")
