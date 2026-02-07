from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base, ClubScopedMixin

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    """Base service with automatic club_id scoping for multi-tenancy."""

    def __init__(self, model: type[ModelType], db: AsyncSession, club_id: UUID):
        self.model = model
        self.db = db
        self.club_id = club_id

    def _scoped_query(self) -> Select:
        stmt = select(self.model)
        if issubclass(self.model, ClubScopedMixin):
            stmt = stmt.where(self.model.club_id == self.club_id)  # type: ignore[attr-defined]
        return stmt

    async def get_by_id(self, entity_id: UUID) -> ModelType | None:
        stmt = self._scoped_query().where(self.model.id == entity_id)  # type: ignore[attr-defined]
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, *, offset: int = 0, limit: int = 20) -> list[ModelType]:
        stmt = self._scoped_query().offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        if issubclass(self.model, ClubScopedMixin):
            stmt = stmt.where(self.model.club_id == self.club_id)  # type: ignore[attr-defined]
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs) -> ModelType:
        if issubclass(self.model, ClubScopedMixin):
            kwargs["club_id"] = self.club_id
        entity = self.model(**kwargs)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity_id: UUID, **kwargs) -> ModelType | None:
        entity = await self.get_by_id(entity_id)
        if not entity:
            return None
        for key, value in kwargs.items():
            if value is not None:
                setattr(entity, key, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        entity = await self.get_by_id(entity_id)
        if not entity:
            return False
        await self.db.delete(entity)
        await self.db.flush()
        return True
