from typing import Any, Generic, List, Optional, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Base
from app.infra.repositories.base import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)


class CRUDService(Generic[ModelType]):
    """Serviço genérico de CRUD para operações básicas sem regras de negócio."""

    def __init__(self, repository: BaseRepository[ModelType]):
        self.repository = repository

    async def get_by_id(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        return await self.repository.get_by_id(session, id)

    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return await self.repository.get_all(session, skip=skip, limit=limit)

    async def create(self, session: AsyncSession, obj_in: Any) -> ModelType:
        return await self.repository.create(session, obj_in)

    async def update(self, session: AsyncSession, id: Any, obj_in: Any) -> Optional[ModelType]:
        db_obj = await self.repository.get_by_id(session, id)
        if not db_obj:
            return None
        return await self.repository.update(session, db_obj, obj_in)

    async def delete(self, session: AsyncSession, id: Any) -> bool:
        return await self.repository.delete(session, id)
