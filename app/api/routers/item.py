from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.domain.schemas import ItemCreate, ItemResponse
from app.services.item_service import ItemService

router = APIRouter(prefix="/items", tags=["Items"])


@router.post(
    "",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um novo Item com evento Outbox",
)
async def create_item(
    item_in: ItemCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ItemResponse:
    """
    Endpoint HTTP da API v1 para criação de Item.
    Clean Architecture: Lida exclusivamente com HTTP, delegando a regra para a camada Service.
    """
    service = ItemService()
    return await service.create_item(session=session, item_data=item_in)
