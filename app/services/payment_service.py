from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payment import Payment
from app.models.player import Player
from app.services.base import BaseService


class PaymentService(BaseService[Payment]):
    def __init__(self, db: AsyncSession, club_id: UUID):
        super().__init__(model=Payment, db=db, club_id=club_id)

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> list[Payment]:
        stmt = (
            self._scoped_query()
            .order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_for_player(self, player_id: UUID) -> list[Payment]:
        stmt = (
            self._scoped_query()
            .where(Payment.player_id == player_id)
            .order_by(Payment.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_pending_for_player(self, player_id: UUID) -> list[Payment]:
        stmt = (
            self._scoped_query()
            .where(
                Payment.player_id == player_id,
                Payment.status.in_(["pending", "overdue"]),
            )
            .order_by(Payment.due_date.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_finance_summary(self) -> dict:
        base = select(Payment).where(Payment.club_id == self.club_id).subquery()

        total_received = await self.db.execute(
            select(func.coalesce(func.sum(base.c.amount), 0)).where(
                base.c.status == "paid"
            )
        )
        total_pending = await self.db.execute(
            select(func.coalesce(func.sum(base.c.amount), 0)).where(
                base.c.status == "pending"
            )
        )
        total_overdue = await self.db.execute(
            select(func.coalesce(func.sum(base.c.amount), 0)).where(
                base.c.status == "overdue"
            )
        )
        total_waived = await self.db.execute(
            select(func.coalesce(func.sum(base.c.amount), 0)).where(
                base.c.status == "waived"
            )
        )

        player_count_result = await self.db.execute(
            select(func.count(func.distinct(base.c.player_id)))
        )
        paid_player_count_result = await self.db.execute(
            select(func.count(func.distinct(base.c.player_id))).where(
                base.c.status == "paid"
            )
        )

        return {
            "total_received": total_received.scalar_one(),
            "total_pending": total_pending.scalar_one(),
            "total_overdue": total_overdue.scalar_one(),
            "total_waived": total_waived.scalar_one(),
            "player_count": player_count_result.scalar_one(),
            "paid_player_count": paid_player_count_result.scalar_one(),
        }

    async def get_player_payment_summaries(self) -> list[dict]:
        stmt = (
            select(
                Payment.player_id,
                Player.name.label("player_name"),
                func.coalesce(
                    func.sum(
                        case((Payment.status == "paid", Payment.amount), else_=Decimal(0))
                    ),
                    0,
                ).label("total_paid"),
                func.coalesce(
                    func.sum(
                        case(
                            (Payment.status == "pending", Payment.amount), else_=Decimal(0)
                        )
                    ),
                    0,
                ).label("total_pending"),
                func.coalesce(
                    func.sum(
                        case(
                            (Payment.status == "overdue", Payment.amount), else_=Decimal(0)
                        )
                    ),
                    0,
                ).label("total_overdue"),
                func.max(
                    case((Payment.status == "paid", Payment.paid_date), else_=None)
                ).label("last_payment_date"),
            )
            .join(Player, Payment.player_id == Player.id)
            .where(Payment.club_id == self.club_id)
            .group_by(Payment.player_id, Player.name)
            .order_by(Player.name)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "player_id": row.player_id,
                "player_name": row.player_name,
                "total_paid": row.total_paid,
                "total_pending": row.total_pending,
                "total_overdue": row.total_overdue,
                "last_payment_date": row.last_payment_date,
            }
            for row in rows
        ]

    async def waive_payment(self, payment_id: UUID, reason: str) -> Payment | None:
        payment = await self.get_by_id(payment_id)
        if not payment:
            return None
        payment.status = "waived"
        payment.waived_reason = reason
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def reduce_payment(
        self, payment_id: UUID, new_amount: Decimal, reason: str
    ) -> Payment | None:
        payment = await self.get_by_id(payment_id)
        if not payment:
            return None
        payment.reduced_from = payment.amount
        payment.amount = new_amount
        payment.reduce_reason = reason
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def reconcile_payment(
        self, payment_id: UUID, bank_reference: str, received_date: date
    ) -> Payment | None:
        payment = await self.get_by_id(payment_id)
        if not payment:
            return None
        payment.status = "paid"
        payment.bank_reference = bank_reference
        payment.received_date = received_date
        payment.paid_date = received_date
        await self.db.flush()
        await self.db.refresh(payment)
        return payment

    async def update_status(
        self, payment_id: UUID, status: str, paid_date: date | None = None
    ) -> Payment | None:
        payment = await self.get_by_id(payment_id)
        if not payment:
            return None
        payment.status = status
        if paid_date:
            payment.paid_date = paid_date
        await self.db.flush()
        await self.db.refresh(payment)
        return payment
