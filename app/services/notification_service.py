from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match
from app.models.match_availability import MatchAvailability
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.player import Player


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_user(self, user_id: UUID, *, limit: int = 50) -> list[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        stmt = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def mark_read(self, notification_id: UUID) -> bool:
        stmt = (
            update(Notification)
            .where(Notification.id == notification_id)
            .values(is_read=True)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def mark_all_read(self, user_id: UUID) -> bool:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        await self.db.execute(stmt)
        await self.db.flush()
        return True

    async def create_notification(
        self,
        club_id: UUID,
        user_id: UUID,
        type: str,
        title: str,
        body: str | None = None,
        data: dict | None = None,
    ) -> Notification:
        notif = Notification(
            club_id=club_id,
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=data or {},
        )
        self.db.add(notif)
        await self.db.flush()
        await self.db.refresh(notif)
        return notif

    async def generate_match_reminders(self) -> int:
        """Generate reminders for upcoming matches within 48 hours."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=48)

        # Find upcoming matches within 48h that don't already have reminders
        stmt = (
            select(Match)
            .where(
                Match.status == "upcoming",
                Match.date <= cutoff.date(),
                Match.date >= now.date(),
            )
        )
        result = await self.db.execute(stmt)
        matches = list(result.scalars().all())

        count = 0
        for match in matches:
            # Find players without availability set
            avail_stmt = select(MatchAvailability.player_id).where(
                MatchAvailability.match_id == match.id
            )
            avail_result = await self.db.execute(avail_stmt)
            responded_player_ids = {row[0] for row in avail_result.all()}

            # Find all players in this club
            player_stmt = select(Player).where(Player.club_id == match.club_id)
            player_result = await self.db.execute(player_stmt)
            players = list(player_result.scalars().all())

            for player in players:
                if player.id not in responded_player_ids and player.user_id:
                    # Check if we already sent a reminder
                    existing = await self.db.execute(
                        select(func.count())
                        .select_from(Notification)
                        .where(
                            Notification.user_id == player.user_id,
                            Notification.type == "match_reminder",
                            Notification.data["match_id"].as_string() == str(match.id),
                        )
                    )
                    if existing.scalar_one() == 0:
                        await self.create_notification(
                            club_id=match.club_id,
                            user_id=player.user_id,
                            type="match_reminder",
                            title=f"Availability needed: {match.opponent}",
                            body=f"Please set your availability for the match on {match.date}",
                            data={"match_id": str(match.id)},
                        )
                        count += 1
        return count

    async def generate_payment_reminders(self) -> int:
        """Generate reminders for overdue payments."""
        stmt = select(Payment).where(Payment.status == "overdue")
        result = await self.db.execute(stmt)
        payments = list(result.scalars().all())

        count = 0
        for payment in payments:
            # Get the player to find user_id
            player_stmt = select(Player).where(Player.id == payment.player_id)
            player_result = await self.db.execute(player_stmt)
            player = player_result.scalar_one_or_none()
            if not player or not player.user_id:
                continue

            # Check if we already sent a reminder for this payment
            existing = await self.db.execute(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.user_id == player.user_id,
                    Notification.type == "payment_reminder",
                    Notification.data["payment_id"].as_string() == str(payment.id),
                )
            )
            if existing.scalar_one() == 0:
                await self.create_notification(
                    club_id=payment.club_id,
                    user_id=player.user_id,
                    type="payment_reminder",
                    title="Payment overdue",
                    body=f"You have an overdue payment of £{payment.amount}",
                    data={"payment_id": str(payment.id)},
                )
                count += 1
        return count
