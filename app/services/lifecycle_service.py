from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match
from app.models.match_audit_log import MatchAuditLog
from app.models.match_availability import MatchAvailability
from app.models.match_participation import MatchParticipation
from app.models.payment import Payment
from app.models.player import Player
from app.models.profile import Profile
from app.models.team import Team
from app.models.team_selection import TeamSelection


class LifecycleService:
    def __init__(self, db: AsyncSession, club_id: UUID):
        self.db = db
        self.club_id = club_id

    async def get_match_lifecycle(self, match_id: UUID) -> list[dict]:
        """Full lifecycle view of every player for a match."""
        # Get all club players
        player_stmt = (
            select(Player)
            .where(Player.club_id == self.club_id)
            .order_by(Player.name)
        )
        player_result = await self.db.execute(player_stmt)
        players = list(player_result.scalars().all())

        # Availability
        avail_stmt = select(MatchAvailability).where(MatchAvailability.match_id == match_id)
        avail_result = await self.db.execute(avail_stmt)
        avail_map = {a.player_id: a for a in avail_result.scalars().all()}

        # Selections
        sel_stmt = select(TeamSelection).where(TeamSelection.match_id == match_id)
        sel_result = await self.db.execute(sel_stmt)
        sel_map = {s.player_id: s for s in sel_result.scalars().all()}

        # Participation
        part_stmt = select(MatchParticipation).where(MatchParticipation.match_id == match_id)
        part_result = await self.db.execute(part_stmt)
        part_map = {p.player_id: p for p in part_result.scalars().all()}

        # Payments
        pay_stmt = select(Payment).where(
            Payment.club_id == self.club_id,
            Payment.match_id == match_id,
        )
        pay_result = await self.db.execute(pay_stmt)
        pay_map = {p.player_id: p for p in pay_result.scalars().all()}

        lifecycle = []
        for player in players:
            avail = avail_map.get(player.id)
            sel = sel_map.get(player.id)
            part = part_map.get(player.id)
            pay = pay_map.get(player.id)

            lifecycle.append({
                "player_id": player.id,
                "player_name": player.name,
                "player_role": player.role,
                "availability_status": avail.status if avail else None,
                "availability_reason": None,
                "is_selected": sel is not None,
                "selection_status": sel.selection_type if sel else None,
                "not_selected_reason": None,
                "participation_status": part.status if part else None,
                "was_substitute": part.was_substitute if part else False,
                "has_payment": pay is not None,
                "payment_status": pay.status if pay else None,
                "payment_reference": pay.bank_reference if pay else None,
            })

        return lifecycle

    async def get_deadline_alerts(self) -> list[dict]:
        """Upcoming matches with deadlines."""
        now = datetime.now(timezone.utc)
        upcoming_cutoff = now + timedelta(days=7)

        stmt = (
            select(Match, Team.name.label("team_name"))
            .outerjoin(Team, Match.team_id == Team.id)
            .where(
                Match.club_id == self.club_id,
                Match.status == "upcoming",
                Match.date <= upcoming_cutoff.date(),
            )
            .order_by(Match.date.asc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        alerts = []
        for match, team_name in rows:
            # Count available and selected
            avail_count_stmt = select(func.count(MatchAvailability.id)).where(
                MatchAvailability.match_id == match.id,
                MatchAvailability.status == "available",
            )
            sel_count_stmt = select(func.count(TeamSelection.id)).where(
                TeamSelection.match_id == match.id
            )

            avail_count = (await self.db.execute(avail_count_stmt)).scalar_one()
            sel_count = (await self.db.execute(sel_count_stmt)).scalar_one()

            # Deadline is 48h before match
            match_dt = datetime.combine(match.date, match.time, tzinfo=timezone.utc)
            deadline = match_dt - timedelta(hours=48)
            hours_until = max(0.0, (deadline - now).total_seconds() / 3600)

            alerts.append({
                "alert_id": str(uuid4()),
                "match_id": match.id,
                "match_date": match.date.isoformat(),
                "match_description": f"{match.venue} vs {match.opponent}",
                "opponent_name": match.opponent,
                "team_name": team_name,
                "deadline_at": deadline.isoformat(),
                "hours_until_deadline": round(hours_until, 1),
                "available_count": avail_count,
                "selected_count": sel_count,
                "target_players": 11,
            })

        return alerts

    async def get_audit_log(
        self, match_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[dict]:
        stmt = (
            select(
                MatchAuditLog,
                Player.name.label("player_name"),
                Profile.display_name.label("actor_name"),
            )
            .outerjoin(Player, MatchAuditLog.player_id == Player.id)
            .outerjoin(Profile, MatchAuditLog.actor_id == Profile.id)
            .where(MatchAuditLog.match_id == match_id)
            .order_by(MatchAuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": entry.id,
                "player_id": entry.player_id,
                "player_name": player_name,
                "action": entry.action,
                "previous_state": entry.previous_state,
                "new_state": entry.new_state,
                "actor_id": entry.actor_id,
                "actor_name": actor_name,
                "actor_type": "admin",
                "reason": entry.reason,
                "details": entry.details,
                "created_at": entry.created_at,
            }
            for entry, player_name, actor_name in rows
        ]

    async def get_participation(self, match_id: UUID) -> list[dict]:
        stmt = (
            select(
                MatchParticipation,
                Player.name.label("player_name"),
                Player.role.label("player_role"),
            )
            .join(Player, MatchParticipation.player_id == Player.id)
            .where(MatchParticipation.match_id == match_id)
            .order_by(Player.name)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": p.id,
                "match_id": p.match_id,
                "player_id": p.player_id,
                "player_name": pname,
                "player_role": prole,
                "status": p.status,
                "was_substitute": p.was_substitute,
                "substitute_for_player_id": p.substitute_for_player_id,
                "substitute_for_player_name": None,
                "withdrawal_reason": p.withdrawal_reason,
                "no_show_reason": p.no_show_reason,
                "confirmed_at": p.confirmed_at,
            }
            for p, pname, prole in rows
        ]

    async def get_played_match_ids(self, player_id: UUID) -> list[str]:
        stmt = (
            select(MatchParticipation.match_id)
            .where(
                MatchParticipation.player_id == player_id,
                MatchParticipation.status == "played",
            )
        )
        result = await self.db.execute(stmt)
        return [str(r[0]) for r in result.all()]

    async def confirm_participation(
        self, match_id: UUID, participations: list[dict], actor_id: UUID | None = None
    ) -> dict:
        for p_data in participations:
            player_id = p_data["player_id"]

            # Upsert participation
            stmt = select(MatchParticipation).where(
                MatchParticipation.match_id == match_id,
                MatchParticipation.player_id == player_id,
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.status = p_data["status"]
                existing.was_substitute = p_data.get("was_substitute", False)
                existing.substitute_for_player_id = p_data.get("substitute_for_player_id")
                existing.no_show_reason = p_data.get("no_show_reason")
            else:
                entry = MatchParticipation(
                    match_id=match_id,
                    player_id=player_id,
                    status=p_data["status"],
                    was_substitute=p_data.get("was_substitute", False),
                    substitute_for_player_id=p_data.get("substitute_for_player_id"),
                    no_show_reason=p_data.get("no_show_reason"),
                )
                self.db.add(entry)

            # Audit log
            audit = MatchAuditLog(
                match_id=match_id,
                player_id=player_id,
                action="confirm_participation",
                new_state=p_data["status"],
                actor_id=actor_id,
            )
            self.db.add(audit)

        await self.db.flush()
        return {"success": True}

    async def record_withdrawal(
        self, match_id: UUID, player_id: UUID, reason: str, actor_id: UUID | None = None
    ) -> dict:
        # Check existing participation
        stmt = select(MatchParticipation).where(
            MatchParticipation.match_id == match_id,
            MatchParticipation.player_id == player_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.status = "withdrawn"
            existing.withdrawal_reason = reason
        else:
            entry = MatchParticipation(
                match_id=match_id,
                player_id=player_id,
                status="withdrawn",
                withdrawal_reason=reason,
            )
            self.db.add(entry)

        audit = MatchAuditLog(
            match_id=match_id,
            player_id=player_id,
            action="withdrawal",
            new_state="withdrawn",
            actor_id=actor_id,
            reason=reason,
        )
        self.db.add(audit)
        await self.db.flush()
        return {"success": True}

    async def add_substitute(
        self,
        match_id: UUID,
        player_id: UUID,
        replaces_player_id: UUID | None = None,
        actor_id: UUID | None = None,
    ) -> dict:
        entry = MatchParticipation(
            match_id=match_id,
            player_id=player_id,
            status="substitute",
            was_substitute=True,
            substitute_for_player_id=replaces_player_id,
        )
        self.db.add(entry)

        audit = MatchAuditLog(
            match_id=match_id,
            player_id=player_id,
            action="substitute_added",
            new_state="substitute",
            actor_id=actor_id,
            details={"replaces_player_id": str(replaces_player_id)} if replaces_player_id else {},
        )
        self.db.add(audit)
        await self.db.flush()
        return {"success": True}

    async def finalize_selection(self, match_id: UUID, actor_id: UUID | None = None) -> dict:
        """Mark all selected players as confirmed participants."""
        sel_stmt = select(TeamSelection.player_id).where(
            TeamSelection.match_id == match_id
        )
        sel_result = await self.db.execute(sel_stmt)
        player_ids = [r[0] for r in sel_result.all()]

        for pid in player_ids:
            stmt = select(MatchParticipation).where(
                MatchParticipation.match_id == match_id,
                MatchParticipation.player_id == pid,
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                entry = MatchParticipation(
                    match_id=match_id,
                    player_id=pid,
                    status="played",
                )
                self.db.add(entry)

        audit = MatchAuditLog(
            match_id=match_id,
            action="finalize_selection",
            new_state="finalized",
            actor_id=actor_id,
            details={"player_count": len(player_ids)},
        )
        self.db.add(audit)
        await self.db.flush()
        return {"success": True}

    async def record_abandoned(
        self, match_id: UUID, reason: str | None = None, actor_id: UUID | None = None
    ) -> dict:
        # Update match status
        match_stmt = select(Match).where(Match.id == match_id)
        match_result = await self.db.execute(match_stmt)
        match = match_result.scalar_one_or_none()
        if match:
            match.status = "cancelled"
            match.result = "abandoned"

        # Update all participation to match_abandoned
        part_stmt = select(MatchParticipation).where(
            MatchParticipation.match_id == match_id
        )
        part_result = await self.db.execute(part_stmt)
        for p in part_result.scalars().all():
            p.status = "match_abandoned"

        audit = MatchAuditLog(
            match_id=match_id,
            action="match_abandoned",
            new_state="abandoned",
            actor_id=actor_id,
            reason=reason,
        )
        self.db.add(audit)
        await self.db.flush()
        return {"success": True}

    async def get_selection_stats(self, player_id: UUID) -> dict:
        """Stats for a player's selection history."""
        # Matches available
        avail_stmt = select(func.count(MatchAvailability.id)).where(
            MatchAvailability.player_id == player_id,
            MatchAvailability.status == "available",
        )
        avail_count = (await self.db.execute(avail_stmt)).scalar_one()

        # Matches selected
        sel_stmt = select(func.count(TeamSelection.id)).where(
            TeamSelection.player_id == player_id,
        )
        sel_count = (await self.db.execute(sel_stmt)).scalar_one()

        # Matches played
        played_stmt = select(func.count(MatchParticipation.id)).where(
            MatchParticipation.player_id == player_id,
            MatchParticipation.status == "played",
        )
        played_count = (await self.db.execute(played_stmt)).scalar_one()

        # No shows
        noshow_stmt = select(func.count(MatchParticipation.id)).where(
            MatchParticipation.player_id == player_id,
            MatchParticipation.status == "no_show",
        )
        noshow_count = (await self.db.execute(noshow_stmt)).scalar_one()

        # Withdrawals
        withdrawal_stmt = select(func.count(MatchParticipation.id)).where(
            MatchParticipation.player_id == player_id,
            MatchParticipation.status == "withdrawn",
        )
        withdrawal_count = (await self.db.execute(withdrawal_stmt)).scalar_one()

        selection_rate = round(sel_count / avail_count * 100, 1) if avail_count > 0 else 0.0

        return {
            "player_id": player_id,
            "matches_available": avail_count,
            "matches_selected": sel_count,
            "matches_played": played_count,
            "selection_rate": selection_rate,
            "no_shows": noshow_count,
            "withdrawals": withdrawal_count,
            "late_withdrawals": 0,
        }
