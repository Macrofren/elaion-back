from typing import Any, List, Type, TypeVar
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db_session
from app.domain.models import Base
from app.infra.repositories.base import BaseRepository
from app.services.crud_service import CRUDService

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


def create_crud_router(
    model: Type[ModelType],
    create_schema: Type[CreateSchemaType],
    update_schema: Type[UpdateSchemaType],
    response_schema: Type[ResponseSchemaType],
    prefix: str,
    tags: List[str],
) -> APIRouter:
    """Factory que gera um APIRouter com os endpoints CRUD básicos para qualquer entidade ORM."""
    router = APIRouter(prefix=prefix, tags=tags)
    repository = BaseRepository(model)
    service = CRUDService(repository)

    @router.post("", response_model=response_schema, status_code=status.HTTP_201_CREATED)
    async def create(
        item_in: create_schema,
        session: AsyncSession = Depends(get_db_session),
    ):
        return await service.create(session, item_in)

    @router.get("", response_model=List[response_schema])
    async def list_all(
        skip: int = 0,
        limit: int = 100,
        session: AsyncSession = Depends(get_db_session),
    ):
        return await service.get_all(session, skip=skip, limit=limit)

    @router.get("/{id}", response_model=response_schema)
    async def get_by_id(
        id: int,
        session: AsyncSession = Depends(get_db_session),
    ):
        db_obj = await service.get_by_id(session, id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro '{model.__tablename__}' com ID {id} não foi encontrado.",
            )
        return db_obj

    @router.put("/{id}", response_model=response_schema)
    async def update(
        id: int,
        item_in: update_schema,
        session: AsyncSession = Depends(get_db_session),
    ):
        db_obj = await service.update(session, id, item_in)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro '{model.__tablename__}' com ID {id} não foi encontrado para atualização.",
            )
        return db_obj

    @router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete(
        id: int,
        session: AsyncSession = Depends(get_db_session),
    ):
        success = await service.delete(session, id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Registro '{model.__tablename__}' com ID {id} não foi encontrado para exclusão.",
            )
        return None

    return router
