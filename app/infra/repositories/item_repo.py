from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Item, OutboxEvent
from app.domain.schemas import ItemCreate
from app.infra.repositories.base import BaseRepository


class ItemRepository(BaseRepository[Item]):
    """Repositório específico para Item e gravação Transactional Outbox."""

    def __init__(self):
        super().__init__(Item)

    async def create_item_with_event(
        self, session: AsyncSession, item_data: ItemCreate
    ) -> Tuple[Item, OutboxEvent]:
        """
        Insere o Item e o OutboxEvent na MESMA transação do banco de dados (Transactional Outbox Pattern).
        Garante atomicidade da operação de escrita de negócio com o evento.
        """
        # 1. Instanciar Entidade de Domínio Principal
        db_item = Item(
            name=item_data.name,
            description=item_data.description,
        )
        session.add(db_item)
        await session.flush()  # Gera a PK UUIDv7 antes de criar o evento

        # 2. Instanciar Evento de Outbox na mesma transação
        event_payload = {
            "item_id": str(db_item.id),
            "name": db_item.name,
            "description": db_item.description,
        }
        outbox_event = OutboxEvent(
            event_type="ITEM_CREATED",
            payload=event_payload,
            status="PENDING",
        )
        session.add(outbox_event)

        # 3. Commit transacional atômico
        await session.commit()
        await session.refresh(db_item)
        await session.refresh(outbox_event)

        return db_item, outbox_event
