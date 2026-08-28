from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Repositório base genérico assíncrono para operações CRUD puras."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """Busca um registro pela Chave Primária."""
        result = await session.execute(select(self.model).where(self.model.id == id))
        return result.scalars().first()

    async def get_all(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Lista registros com suporte a paginação simples."""
        result = await session.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, obj_in: Any) -> ModelType:
        """Cria um novo registro a partir de um DTO Pydantic ou dicionário."""
        if isinstance(obj_in, dict):
            create_data = obj_in
        else:
            create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.model(**create_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(self, session: AsyncSession, db_obj: ModelType, obj_in: Any) -> ModelType:
        """Atualiza um registro existente com os dados fornecidos."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def delete(self, session: AsyncSession, id: Any) -> bool:
        """Remove um registro por ID."""
        db_obj = await self.get_by_id(session, id)
        if db_obj:
            await session.delete(db_obj)
            await session.commit()
            return True
        return False
