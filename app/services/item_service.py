from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.schemas import ItemCreate, ItemResponse
from app.infra.repositories.item_repo import ItemRepository


class ItemService:
    """
    Camada de Serviço (Casos de Uso e Regras de Negócio Puras).
    Clean Architecture: Totalmente isolada de bibliotecas web (FastAPI/Request/HTTPException).
    """

    def __init__(self, item_repo: ItemRepository | None = None):
        self.item_repo = item_repo or ItemRepository()

    async def create_item(self, session: AsyncSession, item_data: ItemCreate) -> ItemResponse:
        """
        Executa o caso de uso de criação de item e emissão de evento de Outbox.
        """
        # Execução do repositório
        db_item, _outbox_event = await self.item_repo.create_item_with_event(
            session=session,
            item_data=item_data,
        )

        # Conversão DTO Fail-Fast para a camada HTTP
        return ItemResponse.model_validate(db_item)
