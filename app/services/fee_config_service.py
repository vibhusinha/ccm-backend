from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fee_config import FeeConfig

DEFAULT_FEES = {
    "membership_fee": Decimal("150.00"),
    "match_fee": Decimal("15.00"),
    "nets_fee": Decimal("5.00"),
    "meeting_fee": Decimal("10.00"),
    "event_fee": Decimal("0.00"),
    "merchandise_fee": Decimal("0.00"),
}


class FeeConfigService:
    def __init__(self, db: AsyncSession, club_id: UUID):
        self.db = db
        self.club_id = club_id

    async def get_config(self) -> dict:
        stmt = select(FeeConfig).where(FeeConfig.club_id == self.club_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            return {
                "membership": config.membership_fee,
                "match": config.match_fee,
                "nets": config.nets_fee,
                "meeting": config.meeting_fee,
                "event": config.event_fee,
                "merchandise": config.merchandise_fee,
            }

        return {
            "membership": DEFAULT_FEES["membership_fee"],
            "match": DEFAULT_FEES["match_fee"],
            "nets": DEFAULT_FEES["nets_fee"],
            "meeting": DEFAULT_FEES["meeting_fee"],
            "event": DEFAULT_FEES["event_fee"],
            "merchandise": DEFAULT_FEES["merchandise_fee"],
        }

    async def upsert_config(self, **kwargs) -> dict:
        stmt = select(FeeConfig).where(FeeConfig.club_id == self.club_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            for key, value in kwargs.items():
                if value is not None and hasattr(config, key):
                    setattr(config, key, value)
        else:
            data = {k: v for k, v in DEFAULT_FEES.items()}
            for key, value in kwargs.items():
                if value is not None and key in data:
                    data[key] = value
            config = FeeConfig(club_id=self.club_id, **data)
            self.db.add(config)

        await self.db.flush()
        await self.db.refresh(config)

        return {
            "membership": config.membership_fee,
            "match": config.match_fee,
            "nets": config.nets_fee,
            "meeting": config.meeting_fee,
            "event": config.event_fee,
            "merchandise": config.merchandise_fee,
        }
