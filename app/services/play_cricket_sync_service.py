from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.play_cricket_client import PlayCricketClient
from app.integrations.play_cricket_mappers import (
    map_batting_entry,
    map_bowling_entry,
    map_innings,
    map_match,
    map_player,
    map_team,
)
from app.models.batting_entry import BattingEntry
from app.models.bowling_entry import BowlingEntry
from app.models.fall_of_wicket import FallOfWicket
from app.models.match import Match
from app.models.match_innings import MatchInnings
from app.models.match_opposition_player import MatchOppositionPlayer
from app.models.player import Player
from app.models.team import Team
from app.schemas.play_cricket import SyncAllResult, SyncResult

logger = logging.getLogger(__name__)


class PlayCricketSyncService:
    def __init__(self, db: AsyncSession, club_id: UUID, client: PlayCricketClient):
        self.db = db
        self.club_id = club_id
        self.client = client

    # ------------------------------------------------------------------
    # Teams
    # ------------------------------------------------------------------

    async def sync_teams(self, site_id: int) -> SyncResult:
        result = SyncResult()
        try:
            pc_teams = await self.client.get_teams(site_id)
        except Exception as e:
            result.errors.append(f"API error fetching teams: {e}")
            return result

        for pc_team in pc_teams:
            try:
                pc_id = int(pc_team["id"])
                mapped = map_team(pc_team, self.club_id)

                existing = await self._find_team_by_pc_id(pc_id)
                if existing:
                    existing.name = mapped["name"]
                    existing.is_active = mapped["is_active"]
                    result.updated += 1
                else:
                    team = Team(**mapped)
                    self.db.add(team)
                    result.created += 1
            except Exception as e:
                result.errors.append(f"Team {pc_team.get('id')}: {e}")

        await self.db.flush()
        return result

    # ------------------------------------------------------------------
    # Players
    # ------------------------------------------------------------------

    async def sync_players(self, site_id: int, season: int) -> SyncResult:
        result = SyncResult()
        try:
            pc_players = await self.client.get_players(site_id, season)
        except Exception as e:
            result.errors.append(f"API error fetching players: {e}")
            return result

        for pc_player in pc_players:
            try:
                pc_id = int(pc_player["id"])
                mapped = map_player(pc_player, self.club_id)

                existing = await self._find_player_by_pc_id(pc_id)
                if existing:
                    existing.name = mapped["name"]
                    result.updated += 1
                else:
                    player = Player(**mapped)
                    self.db.add(player)
                    result.created += 1
            except Exception as e:
                result.errors.append(f"Player {pc_player.get('id')}: {e}")

        await self.db.flush()
        return result

    # ------------------------------------------------------------------
    # Matches
    # ------------------------------------------------------------------

    async def sync_matches(self, site_id: int, season: int) -> SyncResult:
        result = SyncResult()
        try:
            pc_matches = await self.client.get_matches(site_id, season)
        except Exception as e:
            result.errors.append(f"API error fetching matches: {e}")
            return result

        team_lookup = await self._build_team_lookup()

        for pc_match in pc_matches:
            try:
                pc_id = int(pc_match["id"])
                mapped = map_match(pc_match, self.club_id, site_id, team_lookup)

                existing = await self._find_match_by_pc_id(pc_id)
                if existing:
                    for key in ("date", "time", "opponent", "venue", "type",
                                "status", "result", "location_name", "team_id"):
                        val = mapped.get(key)
                        if val is not None:
                            setattr(existing, key, val)
                    result.updated += 1
                else:
                    match = Match(**mapped)
                    self.db.add(match)
                    result.created += 1
            except Exception as e:
                result.errors.append(f"Match {pc_match.get('id')}: {e}")

        await self.db.flush()
        return result

    # ------------------------------------------------------------------
    # Scorecard
    # ------------------------------------------------------------------

    async def sync_match_scorecard(self, site_id: int, match: Match) -> SyncResult:
        result = SyncResult()
        pc_match_id = match.play_cricket_id
        if not pc_match_id:
            result.errors.append("Match has no play_cricket_id")
            return result

        try:
            detail = await self.client.get_match_detail(site_id, pc_match_id)
        except Exception as e:
            result.errors.append(f"API error fetching scorecard: {e}")
            return result

        # Clear existing scoring data for this match
        await self._clear_scorecard(match.id)

        # Determine which team is "home" (ours)
        home_team_id = self._extract_home_team_id(detail, site_id)

        # Build player lookup: play_cricket_id -> Player.id
        player_lookup = await self._build_player_lookup()

        # Process innings
        pc_innings_list = detail.get("innings", [])
        for pc_inn in pc_innings_list:
            try:
                inn_data = map_innings(pc_inn, match.id, home_team_id)
                innings = MatchInnings(**inn_data)
                self.db.add(innings)
                await self.db.flush()
                await self.db.refresh(innings)
                result.created += 1

                is_home_batting = inn_data["batting_team"] == "home"

                # Batting entries
                for pc_bat in pc_inn.get("bat", []):
                    bat_data = map_batting_entry(pc_bat, innings.id)
                    batsman_pc_id = pc_bat.get("batsman_id")
                    batsman_name = pc_bat.get("batsman_name", "Unknown")

                    if is_home_batting:
                        bat_data["player_id"] = self._resolve_player_id(
                            batsman_pc_id, player_lookup
                        )
                    else:
                        opp = await self._find_or_create_opposition_player(
                            match.id, batsman_name
                        )
                        bat_data["opposition_player_id"] = opp.id

                    entry = BattingEntry(**bat_data)
                    self.db.add(entry)

                # Bowling entries
                for pc_bowl in pc_inn.get("bowl", []):
                    bowl_data = map_bowling_entry(pc_bowl, innings.id)
                    bowler_pc_id = pc_bowl.get("bowler_id")
                    bowler_name = pc_bowl.get("bowler_name", "Unknown")

                    if not is_home_batting:
                        # Home team bowled in this innings
                        bowl_data["player_id"] = self._resolve_player_id(
                            bowler_pc_id, player_lookup
                        )
                    else:
                        opp = await self._find_or_create_opposition_player(
                            match.id, bowler_name
                        )
                        bowl_data["opposition_player_id"] = opp.id

                    entry = BowlingEntry(**bowl_data)
                    self.db.add(entry)

                await self.db.flush()

            except Exception as e:
                result.errors.append(f"Innings {pc_inn.get('innings_number')}: {e}")

        # Update match result fields
        result_desc = detail.get("result_description", "")
        if result_desc:
            match.result = result_desc
            match.status = "completed"

        toss = detail.get("toss", "")
        if toss:
            match.toss_decision = toss

        batted_first = detail.get("batted_first")
        toss_won_by = detail.get("toss_won_by_team_id")
        if batted_first is not None and home_team_id is not None:
            try:
                match.home_batted_first = int(batted_first) == home_team_id
            except (ValueError, TypeError):
                pass

        if toss_won_by is not None and home_team_id is not None:
            try:
                match.toss_won_by = (
                    "home" if int(toss_won_by) == home_team_id else "opposition"
                )
            except (ValueError, TypeError):
                pass

        # Build score strings from innings
        await self._update_scores_from_innings(match)

        await self.db.flush()
        return result

    # ------------------------------------------------------------------
    # Sync All
    # ------------------------------------------------------------------

    async def sync_all(self, site_id: int, season: int) -> SyncAllResult:
        teams_result = await self.sync_teams(site_id)
        players_result = await self.sync_players(site_id, season)
        matches_result = await self.sync_matches(site_id, season)
        return SyncAllResult(
            teams=teams_result,
            players=players_result,
            matches=matches_result,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _find_team_by_pc_id(self, pc_id: int) -> Team | None:
        stmt = select(Team).where(
            Team.club_id == self.club_id,
            Team.play_cricket_id == pc_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_player_by_pc_id(self, pc_id: int) -> Player | None:
        stmt = select(Player).where(
            Player.club_id == self.club_id,
            Player.play_cricket_id == pc_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_match_by_pc_id(self, pc_id: int) -> Match | None:
        stmt = select(Match).where(
            Match.club_id == self.club_id,
            Match.play_cricket_id == pc_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _build_team_lookup(self) -> dict[int, UUID]:
        stmt = select(Team.play_cricket_id, Team.id).where(
            Team.club_id == self.club_id,
            Team.play_cricket_id.is_not(None),
        )
        result = await self.db.execute(stmt)
        return {int(pc_id): team_id for pc_id, team_id in result.all()}

    async def _build_player_lookup(self) -> dict[int, UUID]:
        stmt = select(Player.play_cricket_id, Player.id).where(
            Player.club_id == self.club_id,
            Player.play_cricket_id.is_not(None),
        )
        result = await self.db.execute(stmt)
        return {int(pc_id): player_id for pc_id, player_id in result.all()}

    async def _clear_scorecard(self, match_id: UUID) -> None:
        inn_stmt = select(MatchInnings.id).where(MatchInnings.match_id == match_id)
        inn_result = await self.db.execute(inn_stmt)
        innings_ids = [r[0] for r in inn_result.all()]

        if innings_ids:
            await self.db.execute(
                delete(BattingEntry).where(BattingEntry.innings_id.in_(innings_ids))
            )
            await self.db.execute(
                delete(BowlingEntry).where(BowlingEntry.innings_id.in_(innings_ids))
            )
            await self.db.execute(
                delete(FallOfWicket).where(FallOfWicket.innings_id.in_(innings_ids))
            )
        await self.db.execute(
            delete(MatchInnings).where(MatchInnings.match_id == match_id)
        )
        await self.db.execute(
            delete(MatchOppositionPlayer).where(
                MatchOppositionPlayer.match_id == match_id
            )
        )
        await self.db.flush()

    async def _find_or_create_opposition_player(
        self, match_id: UUID, name: str
    ) -> MatchOppositionPlayer:
        stmt = select(MatchOppositionPlayer).where(
            MatchOppositionPlayer.match_id == match_id,
            MatchOppositionPlayer.name == name,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        player = MatchOppositionPlayer(match_id=match_id, name=name)
        self.db.add(player)
        await self.db.flush()
        await self.db.refresh(player)
        return player

    def _resolve_player_id(
        self, pc_id: Any, player_lookup: dict[int, UUID]
    ) -> UUID | None:
        if pc_id is None:
            return None
        try:
            return player_lookup.get(int(pc_id))
        except (ValueError, TypeError):
            return None

    def _extract_home_team_id(
        self, detail: dict[str, Any], site_id: int
    ) -> int | None:
        home_club_id = detail.get("home_club_id")
        if home_club_id is not None:
            try:
                if int(home_club_id) == site_id:
                    home_team_id = detail.get("home_team_id")
                    return int(home_team_id) if home_team_id is not None else None
                away_team_id = detail.get("away_team_id")
                return int(away_team_id) if away_team_id is not None else None
            except (ValueError, TypeError):
                pass
        return None

    async def _update_scores_from_innings(self, match: Match) -> None:
        stmt = (
            select(MatchInnings)
            .where(MatchInnings.match_id == match.id)
            .order_by(MatchInnings.innings_number)
        )
        result = await self.db.execute(stmt)
        innings_list = list(result.scalars().all())

        our_parts: list[str] = []
        opp_parts: list[str] = []
        for inn in innings_list:
            score = f"{inn.total_runs}/{inn.total_wickets}"
            if inn.batting_team == "home":
                our_parts.append(score)
            else:
                opp_parts.append(score)

        if our_parts:
            match.our_score = " & ".join(our_parts)
        if opp_parts:
            match.opponent_score = " & ".join(opp_parts)
