import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_and_list_terminal(client: AsyncClient, db_session: AsyncSession):
    """Testa a criação e listagem básica da entidade Terminal."""
    payload = {
        "nome": "Terminal de Teste Maceió",
        "codigo": "TERM-MCZ-01",
        "ativo": True
    }

    # 1. POST /api/v1/terminais
    response_create = await client.post("/api/v1/terminais", json=payload)
    assert response_create.status_code == 201
    data_create = response_create.json()
    assert data_create["nome"] == payload["nome"]
    assert data_create["codigo"] == payload["codigo"]
    terminal_id = data_create["id"]

    # 2. GET /api/v1/terminais/{id}
    response_get = await client.get(f"/api/v1/terminais/{terminal_id}")
    assert response_get.status_code == 200
    assert response_get.json()["id"] == terminal_id

    # 3. GET /api/v1/terminais
    response_list = await client.get("/api/v1/terminais")
    assert response_list.status_code == 200
    assert len(response_list.json()) >= 1


@pytest.mark.asyncio
async def test_create_and_list_congenere(client: AsyncClient, db_session: AsyncSession):
    """Testa a criação e listagem básica da entidade Congenere."""
    payload = {
        "nome": "Distribuidora Mansut Ltda",
        "codigo_sicof": "SIC-88421"
    }

    response_create = await client.post("/api/v1/congeneres", json=payload)
    assert response_create.status_code == 201
    data = response_create.json()
    assert data["nome"] == payload["nome"]
    assert data["codigo_sicof"] == payload["codigo_sicof"]
