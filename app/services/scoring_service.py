from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.batting_entry import BattingEntry
from app.models.bowling_entry import BowlingEntry
from app.models.fall_of_wicket import FallOfWicket
from app.models.fixture_type import FixtureType
from app.models.match import Match
from app.models.match_innings import MatchInnings
from app.models.match_opposition_player import MatchOppositionPlayer
from app.models.player import Player
from app.models.team import Team


class ScoringService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Opposition Players ---

    async def get_opposition_players(self, match_id: UUID) -> list[MatchOppositionPlayer]:
        stmt = (
            select(MatchOppositionPlayer)
            .where(MatchOppositionPlayer.match_id == match_id)
            .order_by(MatchOppositionPlayer.batting_position)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def add_opposition_player(self, match_id: UUID, **kwargs) -> MatchOppositionPlayer:
        player = MatchOppositionPlayer(match_id=match_id, **kwargs)
        self.db.add(player)
        await self.db.flush()
        await self.db.refresh(player)
        return player

    # --- Innings ---

    async def get_innings(self, match_id: UUID) -> list[MatchInnings]:
        stmt = (
            select(MatchInnings)
            .where(MatchInnings.match_id == match_id)
            .order_by(MatchInnings.innings_number)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save_innings(self, match_id: UUID, **kwargs) -> MatchInnings:
        innings_number = kwargs.get("innings_number")
        # Upsert: check if innings already exists
        stmt = select(MatchInnings).where(
            MatchInnings.match_id == match_id,
            MatchInnings.innings_number == innings_number,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        innings = MatchInnings(match_id=match_id, **kwargs)
        self.db.add(innings)
        await self.db.flush()
        await self.db.refresh(innings)
        return innings

    # --- Fall of Wickets ---

    async def save_fall_of_wicket(self, innings_id: UUID, **kwargs) -> FallOfWicket:
        fow = FallOfWicket(innings_id=innings_id, **kwargs)
        self.db.add(fow)
        await self.db.flush()
        await self.db.refresh(fow)
        return fow

    # --- Batting & Bowling Entries ---

    async def get_batting_entries(self, innings_id: UUID) -> list[BattingEntry]:
        stmt = (
            select(BattingEntry)
            .where(BattingEntry.innings_id == innings_id)
            .order_by(BattingEntry.batting_position)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_bowling_entries(self, innings_id: UUID) -> list[BowlingEntry]:
        stmt = (
            select(BowlingEntry)
            .where(BowlingEntry.innings_id == innings_id)
            .order_by(BowlingEntry.bowling_position)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def save_home_player_stats(self, match_id: UUID, data: dict) -> str:
        """Save batting and/or bowling entry for a home player."""
        player_id = data["player_id"]
        innings_id = data.get("innings_id")

        record_id = None

        # Save batting entry if batting data provided
        if data.get("runs_scored") is not None or data.get("batting_position") is not None:
            strike_rate = Decimal("0.00")
            balls = data.get("balls_faced", 0)
            runs = data.get("runs_scored", 0)
            if balls and balls > 0:
                strike_rate = Decimal(str(round(runs / balls * 100, 2)))

            entry = BattingEntry(
                innings_id=innings_id,
                player_id=player_id,
                batting_position=data.get("batting_position"),
                runs_scored=data.get("runs_scored", 0),
                balls_faced=data.get("balls_faced", 0),
                fours=data.get("fours", 0),
                sixes=data.get("sixes", 0),
                dismissal_type=data.get("dismissal_type"),
                how_out=data.get("how_out"),
                not_out=data.get("not_out", False),
                strike_rate=strike_rate,
            )
            self.db.add(entry)
            await self.db.flush()
            await self.db.refresh(entry)
            record_id = str(entry.id)

        # Save bowling entry if bowling data provided
        if data.get("overs_bowled") is not None or data.get("bowling_position") is not None:
            overs = data.get("overs_bowled", Decimal("0"))
            runs_conceded = data.get("runs_conceded", 0)
            economy = Decimal("0.00")
            if overs and float(overs) > 0:
                economy = Decimal(str(round(runs_conceded / float(overs), 2)))

            entry = BowlingEntry(
                innings_id=innings_id,
                player_id=player_id,
                bowling_position=data.get("bowling_position"),
                overs_bowled=overs,
                maidens=data.get("maidens", 0),
                runs_conceded=runs_conceded,
                wickets_taken=data.get("wickets_taken", 0),
                wides=data.get("wides", 0),
                no_balls=data.get("no_balls", 0),
                economy=economy,
            )
            self.db.add(entry)
            await self.db.flush()
            await self.db.refresh(entry)
            record_id = record_id or str(entry.id)

        return record_id or ""

    async def save_opposition_stats(self, match_id: UUID, data: dict) -> str:
        """Save batting and/or bowling entry for an opposition player."""
        opp_id = data["opposition_player_id"]
        innings_id = data.get("innings_id")

        record_id = None

        if data.get("runs_scored") is not None or data.get("batting_position") is not None:
            strike_rate = Decimal("0.00")
            balls = data.get("balls_faced", 0)
            runs = data.get("runs_scored", 0)
            if balls and balls > 0:
                strike_rate = Decimal(str(round(runs / balls * 100, 2)))

            entry = BattingEntry(
                innings_id=innings_id,
                opposition_player_id=opp_id,
                batting_position=data.get("batting_position"),
                runs_scored=data.get("runs_scored", 0),
                balls_faced=data.get("balls_faced", 0),
                fours=data.get("fours", 0),
                sixes=data.get("sixes", 0),
                dismissal_type=data.get("dismissal_type"),
                not_out=False,
                strike_rate=strike_rate,
            )
            self.db.add(entry)
            await self.db.flush()
            await self.db.refresh(entry)
            record_id = str(entry.id)

        if data.get("overs_bowled") is not None or data.get("bowling_position") is not None:
            overs = data.get("overs_bowled", Decimal("0"))
            runs_conceded = data.get("runs_conceded", 0)
            economy = Decimal("0.00")
            if overs and float(overs) > 0:
                economy = Decimal(str(round(runs_conceded / float(overs), 2)))

            entry = BowlingEntry(
                innings_id=innings_id,
                opposition_player_id=opp_id,
                bowling_position=data.get("bowling_position"),
                overs_bowled=overs,
                maidens=data.get("maidens", 0),
                runs_conceded=runs_conceded,
                wickets_taken=data.get("wickets_taken", 0),
                wides=data.get("wides", 0),
                no_balls=data.get("no_balls", 0),
                economy=economy,
            )
            self.db.add(entry)
            await self.db.flush()
            await self.db.refresh(entry)
            record_id = record_id or str(entry.id)

        return record_id or ""

    # --- Match Result ---

    async def update_result(self, match_id: UUID, data: dict) -> Match | None:
        stmt = select(Match).where(Match.id == match_id)
        result = await self.db.execute(stmt)
        match = result.scalar_one_or_none()
        if not match:
            return None

        for key, value in data.items():
            if hasattr(match, key):
                setattr(match, key, value)

        if match.status == "upcoming":
            match.status = "completed"

        await self.db.flush()
        await self.db.refresh(match)
        return match

    # --- Scorecard ---

    async def get_scorecard(self, match_id: UUID) -> dict:
        """Build the full scorecard composite response."""
        # Match info with joins
        stmt = (
            select(
                Match,
                Team.name.label("team_name"),
                FixtureType.name.label("fixture_type_name"),
                Player.name.label("mom_name"),
            )
            .outerjoin(Team, Match.team_id == Team.id)
            .outerjoin(FixtureType, Match.fixture_type_id == FixtureType.id)
            .outerjoin(Player, Match.man_of_match_id == Player.id)
            .where(Match.id == match_id)
        )
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        if not row:
            return {}

        match, team_name, ft_name, mom_name = row

        match_info = {
            "id": match.id,
            "date": match.date.isoformat(),
            "time": match.time.isoformat() if match.time else None,
            "opponent": match.opponent,
            "venue": match.venue,
            "fixture_type": ft_name,
            "team_name": team_name,
            "our_score": match.our_score,
            "opponent_score": match.opponent_score,
            "result": match.result,
            "result_margin": match.result_margin,
            "result_margin_type": match.result_margin_type,
            "toss_won_by": match.toss_won_by,
            "toss_decision": match.toss_decision,
            "home_batted_first": match.home_batted_first,
            "man_of_match_id": str(match.man_of_match_id) if match.man_of_match_id else None,
            "man_of_match_name": mom_name,
            "match_report": match.match_report,
            "status": match.status,
        }

        # Innings
        innings = await self.get_innings(match_id)

        # Opposition players
        opp_players = await self.get_opposition_players(match_id)

        # Batting and bowling entries per innings, split by home/opposition
        home_batting: list[BattingEntry] = []
        home_bowling: list[BowlingEntry] = []
        opp_batting: list[BattingEntry] = []
        opp_bowling: list[BowlingEntry] = []

        for inn in innings:
            bat_entries = await self.get_batting_entries(inn.id)
            bowl_entries = await self.get_bowling_entries(inn.id)

            if inn.batting_team == "home":
                home_batting.extend(bat_entries)
                # Opposition bowled in this innings
                opp_bowling.extend(bowl_entries)
            else:
                opp_batting.extend(bat_entries)
                home_bowling.extend(bowl_entries)

        return {
            "match": match_info,
            "innings": innings,
            "home_batting": home_batting,
            "home_bowling": home_bowling,
            "opposition_players": opp_players,
            "opposition_batting": opp_batting,
            "opposition_bowling": opp_bowling,
        }

    # --- Matches for Scoring ---

    async def get_matches_for_scoring(self, club_id: UUID) -> list[dict]:
        stmt = (
            select(
                Match,
                Team.name.label("team_name"),
                FixtureType.name.label("fixture_type_name"),
            )
            .outerjoin(Team, Match.team_id == Team.id)
            .outerjoin(FixtureType, Match.fixture_type_id == FixtureType.id)
            .where(
                Match.club_id == club_id,
                Match.status.in_(["completed", "in-progress", "upcoming"]),
            )
            .order_by(Match.date.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        # Check which matches have scorecards (have innings)
        match_ids = [r[0].id for r in rows]
        has_scorecard_set: set[UUID] = set()
        if match_ids:
            sc_stmt = (
                select(MatchInnings.match_id)
                .where(MatchInnings.match_id.in_(match_ids))
                .distinct()
            )
            sc_result = await self.db.execute(sc_stmt)
            has_scorecard_set = {r[0] for r in sc_result.all()}

        return [
            {
                "match_id": m.id,
                "match_date": m.date.isoformat(),
                "match_time": m.time.isoformat() if m.time else None,
                "opponent": m.opponent,
                "venue": m.venue,
                "fixture_type": ft_name,
                "team_name": team_name,
                "our_score": m.our_score,
                "opponent_score": m.opponent_score,
                "result": m.result,
                "has_scorecard": m.id in has_scorecard_set,
            }
            for m, team_name, ft_name in rows
        ]

    # --- Delete Scorecard ---

    async def delete_scorecard(self, match_id: UUID) -> bool:
        """Delete all scoring data for a match (innings, entries, FoW, opposition players)."""
        # Get innings ids first
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
            delete(MatchOppositionPlayer).where(MatchOppositionPlayer.match_id == match_id)
        )

        # Reset match result fields
        stmt = select(Match).where(Match.id == match_id)
        result = await self.db.execute(stmt)
        match = result.scalar_one_or_none()
        if match:
            match.result = None
            match.result_margin = None
            match.result_margin_type = None
            match.toss_won_by = None
            match.toss_decision = None
            match.home_batted_first = None

        await self.db.flush()
        return True
