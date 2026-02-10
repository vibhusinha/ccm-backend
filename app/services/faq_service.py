from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faq import FAQ
from app.services.base import BaseService


class FAQService(BaseService[FAQ]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=FAQ, db=db, club_id=club_id)

    async def get_all(
        self, *, offset: int = 0, limit: int = 100, published_only: bool = True
    ) -> list[FAQ]:
        stmt = self._scoped_query().order_by(FAQ.display_order.asc())
        if published_only:
            stmt = stmt.where(FAQ.is_published.is_(True))
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
