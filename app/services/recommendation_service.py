from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.match import Match
from app.models.match_availability import MatchAvailability
from app.models.match_participation import MatchParticipation
from app.models.payment import Payment
from app.models.player import Player
from app.models.player_match_stats import PlayerMatchStats
from app.models.player_selection_override import PlayerSelectionOverride
from app.models.practice_attendance import PracticeAttendance
from app.models.selection_withdrawal import SelectionWithdrawal
from app.models.team import Team
from app.models.team_selection import TeamSelection
from app.models.team_selection_config import TeamSelectionConfig


class RecommendationService:
    def __init__(self, db: AsyncSession, club_id: UUID):
        self.db = db
        self.club_id = club_id

    # --- Config ---

    async def get_config(self) -> TeamSelectionConfig | None:
        stmt = select(TeamSelectionConfig).where(
            TeamSelectionConfig.club_id == self.club_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_config(self, **kwargs) -> TeamSelectionConfig:
        config = await self.get_config()
        if config:
            for key, value in kwargs.items():
                if value is not None:
                    setattr(config, key, value)
        else:
            config = TeamSelectionConfig(club_id=self.club_id, **kwargs)
            self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    # --- Overrides ---

    async def get_overrides(self) -> list[dict]:
        stmt = (
            select(
                PlayerSelectionOverride,
                Player.name.label("player_name"),
                Player.role.label("player_role"),
                Player.is_core.label("is_core"),
            )
            .join(Player, PlayerSelectionOverride.player_id == Player.id)
            .where(PlayerSelectionOverride.club_id == self.club_id)
            .order_by(Player.name)
        )
        result = await self.db.execute(stmt)
        return [
            {
                "id": o.id,
                "player_id": o.player_id,
                "club_id": o.club_id,
                "base_score_override": o.base_score_override,
                "notes": o.notes,
                "player_name": pname,
                "player_role": prole,
                "is_core": is_core,
            }
            for o, pname, prole, is_core in result.all()
        ]

    async def upsert_override(
        self, player_id: UUID, base_score_override: Decimal, notes: str | None = None
    ) -> PlayerSelectionOverride:
        stmt = select(PlayerSelectionOverride).where(
            PlayerSelectionOverride.player_id == player_id,
            PlayerSelectionOverride.club_id == self.club_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.base_score_override = base_score_override
            existing.notes = notes
        else:
            existing = PlayerSelectionOverride(
                player_id=player_id,
                club_id=self.club_id,
                base_score_override=base_score_override,
                notes=notes,
            )
            self.db.add(existing)

        await self.db.flush()
        await self.db.refresh(existing)
        return existing

    async def delete_override(self, override_id: UUID) -> bool:
        stmt = select(PlayerSelectionOverride).where(
            PlayerSelectionOverride.id == override_id,
        )
        result = await self.db.execute(stmt)
        override = result.scalar_one_or_none()
        if not override:
            return False
        await self.db.delete(override)
        await self.db.flush()
        return True

    # --- Player Match Stats ---

    async def get_match_stats(self, match_id: UUID) -> list[dict]:
        stmt = (
            select(
                PlayerMatchStats,
                Player.name.label("player_name"),
                Player.role.label("player_role"),
            )
            .join(Player, PlayerMatchStats.player_id == Player.id)
            .where(PlayerMatchStats.match_id == match_id)
            .order_by(Player.name)
        )
        result = await self.db.execute(stmt)
        return [
            {
                **{c.key: getattr(s, c.key) for c in PlayerMatchStats.__table__.columns},
                "player_name": pname,
                "player_role": prole,
            }
            for s, pname, prole in result.all()
        ]

    async def save_match_stats(
        self, match_id: UUID, player_id: UUID, stats: dict
    ) -> PlayerMatchStats:
        stmt = select(PlayerMatchStats).where(
            PlayerMatchStats.match_id == match_id,
            PlayerMatchStats.player_id == player_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in stats.items():
                if hasattr(existing, key) and value is not None:
                    setattr(existing, key, value)
        else:
            existing = PlayerMatchStats(
                match_id=match_id, player_id=player_id, **stats
            )
            self.db.add(existing)

        await self.db.flush()
        await self.db.refresh(existing)
        return existing

    # --- Player Match History ---

    async def get_player_match_history(
        self, player_id: UUID, limit: int = 10
    ) -> list[dict]:
        stmt = (
            select(PlayerMatchStats, Match.date, Match.opponent, Match.venue)
            .join(Match, PlayerMatchStats.match_id == Match.id)
            .where(PlayerMatchStats.player_id == player_id)
            .order_by(Match.date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return [
            {
                "id": s.id,
                "player_id": s.player_id,
                "match_id": s.match_id,
                "match_date": mdate.isoformat(),
                "opponent": opp,
                "venue": venue,
                "runs_scored": s.runs_scored,
                "balls_faced": s.balls_faced,
                "fours": s.fours,
                "sixes": s.sixes,
                "not_out": s.not_out,
                "batting_position": s.batting_position,
                "how_out": s.how_out,
                "overs_bowled": s.overs_bowled,
                "runs_conceded": s.runs_conceded,
                "wickets": s.wickets,
                "maidens": s.maidens,
                "catches": s.catches,
                "run_outs": s.run_outs,
                "stumpings": s.stumpings,
            }
            for s, mdate, opp, venue in result.all()
        ]

    # --- Practice Attendance ---

    async def record_practice_attendance(
        self, fixture_id: UUID, attendances: list[dict], recorded_by: UUID | None = None
    ) -> bool:
        for att in attendances:
            stmt = select(PracticeAttendance).where(
                PracticeAttendance.fixture_id == fixture_id,
                PracticeAttendance.player_id == att["player_id"],
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                existing.status = att["status"]
                existing.notes = att.get("notes")
            else:
                entry = PracticeAttendance(
                    fixture_id=fixture_id,
                    player_id=att["player_id"],
                    status=att["status"],
                    notes=att.get("notes"),
                    recorded_by=recorded_by,
                )
                self.db.add(entry)

        await self.db.flush()
        return True

    # --- Selection Withdrawal ---

    async def record_selection_withdrawal(
        self, match_id: UUID, player_id: UUID, match_time: str, reason: str | None = None
    ) -> SelectionWithdrawal:
        match_dt = datetime.fromisoformat(match_time)
        now = datetime.now(timezone.utc)

        # Check if late (within configured hours of match)
        config = await self.get_config()
        late_hours = config.late_withdrawal_hours if config else 48
        is_late = (match_dt - now).total_seconds() < late_hours * 3600

        penalty = Decimal("0.00")
        if is_late and config:
            penalty = config.late_withdrawal_penalty

        withdrawal = SelectionWithdrawal(
            match_id=match_id,
            player_id=player_id,
            match_time=match_dt,
            reason=reason,
            is_late=is_late,
            penalty_applied=penalty,
        )
        self.db.add(withdrawal)
        await self.db.flush()
        await self.db.refresh(withdrawal)
        return withdrawal

    # --- Simulation Status ---

    async def get_simulation_status(self) -> dict:
        now = datetime.now(timezone.utc).date()
        upcoming_stmt = (
            select(Match)
            .where(
                Match.club_id == self.club_id,
                Match.status == "upcoming",
                Match.date >= now,
            )
            .order_by(Match.date.asc())
        )
        upcoming_result = await self.db.execute(upcoming_stmt)
        upcoming = list(upcoming_result.scalars().all())

        total = len(upcoming)

        # Check which have selections
        match_ids = [m.id for m in upcoming]
        with_sel = 0
        if match_ids:
            sel_stmt = (
                select(TeamSelection.match_id)
                .where(TeamSelection.match_id.in_(match_ids))
                .distinct()
            )
            sel_result = await self.db.execute(sel_stmt)
            with_sel = len(sel_result.all())

        next_match = upcoming[0] if upcoming else None

        next_has_sel = False
        if next_match:
            check_stmt = select(func.count(TeamSelection.id)).where(
                TeamSelection.match_id == next_match.id
            )
            next_has_sel = (await self.db.execute(check_stmt)).scalar_one() > 0

        return {
            "total_upcoming_matches": total,
            "matches_with_selections": with_sel,
            "matches_without_selections": total - with_sel,
            "next_match_date": next_match.date.isoformat() if next_match else None,
            "next_match_opponent": next_match.opponent if next_match else None,
            "next_match_has_selections": next_has_sel,
        }

    # --- Recommendation Algorithm ---

    async def get_recommendation(self, match_id: UUID) -> list[dict]:
        """Heuristic team recommendation for a match."""
        config = await self.get_config()

        # Weights (use defaults if no config)
        perf_w = float(config.performance_weight) if config else 0.30
        fair_w = float(config.fairness_weight) if config else 0.25
        att_w = float(config.attendance_weight) if config else 0.20
        rel_w = float(config.reliability_weight) if config else 0.15
        dist_w = float(config.season_distribution_weight) if config else 0.10
        base_score = float(config.default_base_score) if config else 50.0

        # Get available players
        avail_stmt = (
            select(MatchAvailability.player_id)
            .where(
                MatchAvailability.match_id == match_id,
                MatchAvailability.status == "available",
            )
        )
        avail_result = await self.db.execute(avail_stmt)
        available_ids = {r[0] for r in avail_result.all()}

        if not available_ids:
            return []

        # Get players
        player_stmt = (
            select(Player)
            .where(Player.club_id == self.club_id, Player.id.in_(available_ids))
            .order_by(Player.name)
        )
        player_result = await self.db.execute(player_stmt)
        players = list(player_result.scalars().all())

        # Overrides map
        override_stmt = select(PlayerSelectionOverride).where(
            PlayerSelectionOverride.club_id == self.club_id
        )
        override_result = await self.db.execute(override_stmt)
        overrides = {o.player_id: o for o in override_result.scalars().all()}

        # Recent stats (last 5 matches per player)
        stats_map: dict[UUID, list] = {}
        for pid in available_ids:
            stmt = (
                select(PlayerMatchStats)
                .join(Match, PlayerMatchStats.match_id == Match.id)
                .where(PlayerMatchStats.player_id == pid)
                .order_by(Match.date.desc())
                .limit(5)
            )
            stats_result = await self.db.execute(stmt)
            stats_map[pid] = list(stats_result.scalars().all())

        # Selection count (fairness)
        sel_count_stmt = (
            select(TeamSelection.player_id, func.count(TeamSelection.id))
            .join(Match, TeamSelection.match_id == Match.id)
            .where(Match.club_id == self.club_id)
            .group_by(TeamSelection.player_id)
        )
        sel_result = await self.db.execute(sel_count_stmt)
        sel_counts = dict(sel_result.all())
        max_sel = max(sel_counts.values()) if sel_counts else 1

        # Practice attendance
        practice_stmt = (
            select(
                PracticeAttendance.player_id,
                func.count(PracticeAttendance.id).filter(
                    PracticeAttendance.status == "attended"
                ),
                func.count(PracticeAttendance.id),
            )
            .group_by(PracticeAttendance.player_id)
        )
        practice_result = await self.db.execute(practice_stmt)
        practice_map = {r[0]: (r[1], r[2]) for r in practice_result.all()}

        # Late withdrawals
        withdrawal_stmt = (
            select(SelectionWithdrawal.player_id, func.count(SelectionWithdrawal.id))
            .where(SelectionWithdrawal.is_late == True)
            .group_by(SelectionWithdrawal.player_id)
        )
        withdrawal_result = await self.db.execute(withdrawal_stmt)
        late_withdrawal_counts = dict(withdrawal_result.all())

        # Payment status
        pay_stmt = (
            select(Payment.player_id, Payment.status)
            .where(Payment.match_id == match_id)
        )
        pay_result = await self.db.execute(pay_stmt)
        pay_map = {r[0]: r[1] for r in pay_result.all()}

        # Score each player
        recommendations = []
        for player in players:
            override = overrides.get(player.id)
            player_base = float(override.base_score_override) if override else base_score

            # Performance score (avg of recent batting + bowling)
            recent = stats_map.get(player.id, [])
            perf_score = 0.0
            bat_score = 0.0
            bowl_score = 0.0
            if recent:
                total_runs = sum(s.runs_scored for s in recent)
                total_wickets = sum(s.wickets for s in recent)
                bat_score = min(total_runs / max(len(recent), 1) / 50 * 100, 100)
                bowl_score = min(total_wickets / max(len(recent), 1) / 3 * 100, 100)
                perf_score = (bat_score + bowl_score) / 2

            # Fairness score (inverse of selection count)
            player_sels = sel_counts.get(player.id, 0)
            fair_score = max(0, 100 - (player_sels / max(max_sel, 1) * 100))

            # Attendance score
            attended, total_practice = practice_map.get(player.id, (0, 0))
            att_score = (attended / max(total_practice, 1)) * 100 if total_practice > 0 else 50

            # Reliability score (inverse of late withdrawals)
            late_count = late_withdrawal_counts.get(player.id, 0)
            rel_score = max(0, 100 - late_count * 20)

            # Season distribution score
            dist_score = fair_score  # Simplified

            composite = (
                player_base
                + perf_score * perf_w
                + fair_score * fair_w
                + att_score * att_w
                + rel_score * rel_w
                + dist_score * dist_w
            )

            recommendations.append({
                "player_id": player.id,
                "player_name": player.name,
                "player_role": player.role,
                "is_paid": pay_map.get(player.id) == "paid",
                "availability_status": "available",
                "performance_score": round(perf_score, 2),
                "fairness_score": round(fair_score, 2),
                "attendance_score": round(att_score, 2),
                "reliability_score": round(rel_score, 2),
                "season_distribution_score": round(dist_score, 2),
                "composite_score": round(composite, 2),
                "batting_score": round(bat_score, 2),
                "bowling_score": round(bowl_score, 2),
                "recommended_batting_position": None,
                "recommended_bowling_position": None,
                "is_recommended": False,
                "recommendation_reason": None,
                "is_reserve": False,
                "reserve_priority": None,
                "base_score": player_base,
                "is_captain": False,
                "is_vice_captain": False,
            })

        # Sort by composite score descending
        recommendations.sort(key=lambda x: x["composite_score"], reverse=True)

        # Role balancing
        role_map = {
            "Batter": {"min": config.min_batters if config else 4, "max": config.max_batters if config else 6},
            "Bowler": {"min": config.min_bowlers if config else 3, "max": config.max_bowlers if config else 5},
            "All-rounder": {"min": config.min_allrounders if config else 1, "max": config.max_allrounders if config else 3},
            "Wicket-keeper": {"min": config.min_keepers if config else 1, "max": config.max_keepers if config else 1},
        }

        selected: list[dict] = []
        reserves: list[dict] = []
        role_counts: dict[str, int] = {"Batter": 0, "Bowler": 0, "All-rounder": 0, "Wicket-keeper": 0}

        # First pass: ensure minimums
        remaining = list(recommendations)
        for role, limits in role_map.items():
            role_players = [r for r in remaining if r["player_role"] == role]
            for p in role_players[:limits["min"]]:
                if len(selected) < 11:
                    p["is_recommended"] = True
                    p["recommendation_reason"] = f"Role minimum ({role})"
                    selected.append(p)
                    role_counts[role] += 1
                    remaining.remove(p)

        # Second pass: fill remaining slots by score
        for p in sorted(remaining, key=lambda x: x["composite_score"], reverse=True):
            role = p["player_role"]
            if len(selected) < 11 and role_counts.get(role, 0) < role_map.get(role, {}).get("max", 11):
                p["is_recommended"] = True
                p["recommendation_reason"] = "Top scorer"
                selected.append(p)
                role_counts[role] = role_counts.get(role, 0) + 1
            elif len(reserves) < 2:
                p["is_reserve"] = True
                p["reserve_priority"] = len(reserves) + 1
                p["recommendation_reason"] = "Reserve"
                reserves.append(p)

        return selected + reserves + [
            r for r in recommendations
            if not r["is_recommended"] and not r["is_reserve"]
        ]

    # --- Clear Selections ---

    async def clear_selections(self, match_id: UUID) -> int:
        count_stmt = select(func.count(TeamSelection.id)).where(
            TeamSelection.match_id == match_id
        )
        count = (await self.db.execute(count_stmt)).scalar_one()

        await self.db.execute(
            delete(TeamSelection).where(TeamSelection.match_id == match_id)
        )
        await self.db.flush()
        return count

    # --- Recommend Next Match ---

    async def recommend_next_match(self, after_date: str | None = None) -> dict:
        now = datetime.now(timezone.utc).date()
        filters = [
            Match.club_id == self.club_id,
            Match.status == "upcoming",
        ]
        if after_date:
            from datetime import date as dt_date
            filters.append(Match.date > dt_date.fromisoformat(after_date))
        else:
            filters.append(Match.date >= now)

        stmt = (
            select(Match, Team.name.label("team_name"))
            .outerjoin(Team, Match.team_id == Team.id)
            .where(*filters)
            .order_by(Match.date.asc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()

        if not row:
            return {
                "match_id": None,
                "match_date": None,
                "opponent": None,
                "team_name": None,
                "players_recommended": 0,
                "message": "No upcoming matches found",
            }

        match, team_name = row
        recommendations = await self.get_recommendation(match.id)
        recommended_count = sum(1 for r in recommendations if r["is_recommended"])

        return {
            "match_id": match.id,
            "match_date": match.date.isoformat(),
            "opponent": match.opponent,
            "team_name": team_name,
            "players_recommended": recommended_count,
        }

    async def reset_selections_first_match(self) -> dict:
        """Clear and re-recommend for the first upcoming match."""
        now = datetime.now(timezone.utc).date()
        stmt = (
            select(Match, Team.name.label("team_name"))
            .outerjoin(Team, Match.team_id == Team.id)
            .where(
                Match.club_id == self.club_id,
                Match.status == "upcoming",
                Match.date >= now,
            )
            .order_by(Match.date.asc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()

        if not row:
            return {
                "match_id": None,
                "match_date": None,
                "opponent": None,
                "team_name": None,
                "players_recommended": 0,
                "message": "No upcoming matches found",
            }

        match, team_name = row
        await self.clear_selections(match.id)
        recommendations = await self.get_recommendation(match.id)
        recommended_count = sum(1 for r in recommendations if r["is_recommended"])

        return {
            "match_id": match.id,
            "match_date": match.date.isoformat(),
            "opponent": match.opponent,
            "team_name": team_name,
            "players_recommended": recommended_count,
        }
