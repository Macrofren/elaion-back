import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Item, OutboxEvent


@pytest.mark.asyncio
async def test_create_item_success(client: AsyncClient, db_session: AsyncSession):
    """
    Testa a criação de Item via rota HTTP POST /api/v1/items:
    1. Retorno HTTP Status Code 201 Created.
    2. Resposta em formato JSON mapeada pelo DTO Pydantic ItemResponse.
    3. Persistência do Item no banco de dados.
    4. Persistência simultânea do evento no Outbox (Transactional Outbox).
    """
    payload = {
        "name": "Item Teste Corporativo",
        "description": "Descrição de teste para validação de arquitetura Clean e Outbox."
    }

    # Executar requisição HTTP POST
    response = await client.post("/api/v1/items", json=payload)

    # 1. Validar HTTP 201 Created
    assert response.status_code == 201

    data = response.json()

    # 2. Validar chaves e dados retornado no Pydantic Response
    assert "id" in data
    assert "name" in data
    assert "description" in data
    assert "created_at" in data
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]

    # 3. Validar se o Item foi gravado no banco de dados
    item_id = data["id"]
    result_item = await db_session.execute(select(Item).where(Item.id == item_id))
    db_item = result_item.scalars().first()
    assert db_item is not None
    assert db_item.name == payload["name"]

    # 4. Validar se o OutboxEvent foi gravado na mesma transação
    result_outbox = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.event_type == "ITEM_CREATED")
    )
    outbox_event = result_outbox.scalars().first()
    assert outbox_event is not None
    assert outbox_event.status == "PENDING"
    assert outbox_event.payload["item_id"] == str(db_item.id)
