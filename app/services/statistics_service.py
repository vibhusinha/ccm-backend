from uuid import UUID

from sqlalchemy import String, case, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fixture_type import FixtureType
from app.models.match import Match
from app.models.match_innings import MatchInnings
from app.models.match_participation import MatchParticipation
from app.models.player import Player
from app.models.team import Team


class StatisticsService:
    def __init__(self, db: AsyncSession, club_id: UUID):
        self.db = db
        self.club_id = club_id

    def _base_match_filter(self):
        return Match.club_id == self.club_id

    async def get_club_statistics(
        self,
        team_id: UUID | None = None,
        season_id: UUID | None = None,
        fixture_type_id: UUID | None = None,
    ) -> dict:
        filters = [self._base_match_filter()]
        if team_id:
            filters.append(Match.team_id == team_id)
        if season_id:
            filters.append(Match.season_id == season_id)
        if fixture_type_id:
            filters.append(Match.fixture_type_id == fixture_type_id)

        stmt = select(
            func.count(Match.id).label("total_matches"),
            func.count(case((Match.status == "completed", 1))).label("completed_matches"),
            func.count(case((Match.result == "won", 1))).label("won"),
            func.count(case((Match.result == "lost", 1))).label("lost"),
            func.count(case((Match.result == "tied", 1))).label("tied"),
            func.count(case((Match.result == "drawn", 1))).label("drawn"),
            func.count(case((Match.result == "abandoned", 1))).label("abandoned"),
            func.count(case((Match.result == "no_result", 1))).label("no_result"),
        ).where(*filters)

        result = await self.db.execute(stmt)
        row = result.one()

        completed = row.completed_matches or 0
        won = row.won or 0
        win_pct = round(won / completed * 100, 1) if completed > 0 else 0.0

        # Total runs scored/conceded from innings
        runs_filters = [MatchInnings.match_id == Match.id, *filters]
        scored_stmt = select(
            func.coalesce(func.sum(MatchInnings.total_runs), 0)
        ).join(Match, MatchInnings.match_id == Match.id).where(
            MatchInnings.batting_team == "home", *filters
        )
        conceded_stmt = select(
            func.coalesce(func.sum(MatchInnings.total_runs), 0)
        ).join(Match, MatchInnings.match_id == Match.id).where(
            MatchInnings.batting_team == "opposition", *filters
        )

        scored_result = await self.db.execute(scored_stmt)
        conceded_result = await self.db.execute(conceded_stmt)

        return {
            "total_matches": row.total_matches,
            "completed_matches": completed,
            "won": won,
            "lost": row.lost or 0,
            "tied": row.tied or 0,
            "drawn": row.drawn or 0,
            "abandoned": row.abandoned or 0,
            "no_result": row.no_result or 0,
            "win_percentage": win_pct,
            "total_runs_scored": scored_result.scalar_one(),
            "total_runs_conceded": conceded_result.scalar_one(),
        }

    async def get_team_statistics(self, season_id: UUID | None = None) -> list[dict]:
        filters = [self._base_match_filter()]
        if season_id:
            filters.append(Match.season_id == season_id)

        stmt = (
            select(
                Match.team_id,
                Team.name.label("team_name"),
                func.count(Match.id).label("total_matches"),
                func.count(case((Match.result == "won", 1))).label("won"),
                func.count(case((Match.result == "lost", 1))).label("lost"),
                func.count(case((Match.result == "tied", 1))).label("tied"),
                func.count(case((Match.result == "drawn", 1))).label("drawn"),
            )
            .join(Team, Match.team_id == Team.id)
            .where(*filters, Match.team_id.isnot(None))
            .group_by(Match.team_id, Team.name)
            .order_by(Team.name)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        teams = []
        for row in rows:
            total = row.total_matches or 0
            won = row.won or 0
            win_pct = round(won / total * 100, 1) if total > 0 else 0.0

            # Recent form: last 5 results
            form_stmt = (
                select(Match.result)
                .where(
                    Match.team_id == row.team_id,
                    Match.result.isnot(None),
                    *filters,
                )
                .order_by(Match.date.desc())
                .limit(5)
            )
            form_result = await self.db.execute(form_stmt)
            form_list = [r[0] for r in form_result.all()]
            form_str = "".join(
                "W" if r == "won" else "L" if r == "lost" else "D" if r == "drawn" else "T" if r == "tied" else "-"
                for r in form_list
            )

            teams.append({
                "team_id": row.team_id,
                "team_name": row.team_name,
                "total_matches": total,
                "won": won,
                "lost": row.lost or 0,
                "tied": row.tied or 0,
                "drawn": row.drawn or 0,
                "win_percentage": win_pct,
                "recent_form": form_str,
            })

        return teams

    async def get_type_statistics(
        self, season_id: UUID | None = None, team_id: UUID | None = None
    ) -> list[dict]:
        filters = [self._base_match_filter()]
        if season_id:
            filters.append(Match.season_id == season_id)
        if team_id:
            filters.append(Match.team_id == team_id)

        stmt = (
            select(
                Match.fixture_type_id,
                FixtureType.name.label("fixture_type_name"),
                func.count(Match.id).label("total_matches"),
                func.count(case((Match.result == "won", 1))).label("won"),
                func.count(case((Match.result == "lost", 1))).label("lost"),
                func.count(case((Match.result == "tied", 1))).label("tied"),
                func.count(case((Match.result == "drawn", 1))).label("drawn"),
            )
            .outerjoin(FixtureType, Match.fixture_type_id == FixtureType.id)
            .where(*filters)
            .group_by(Match.fixture_type_id, FixtureType.name)
            .order_by(FixtureType.name)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "fixture_type_id": row.fixture_type_id,
                "fixture_type_name": row.fixture_type_name,
                "total_matches": row.total_matches or 0,
                "won": row.won or 0,
                "lost": row.lost or 0,
                "tied": row.tied or 0,
                "drawn": row.drawn or 0,
                "win_percentage": round(
                    (row.won or 0) / (row.total_matches or 1) * 100, 1
                ),
            }
            for row in rows
        ]

    async def get_player_records(
        self, player_id: UUID | None = None, season_id: UUID | None = None
    ) -> list[dict]:
        filters = [self._base_match_filter(), MatchParticipation.status == "played"]
        if season_id:
            filters.append(Match.season_id == season_id)
        if player_id:
            filters.append(MatchParticipation.player_id == player_id)

        stmt = (
            select(
                MatchParticipation.player_id,
                Player.name.label("player_name"),
                Team.name.label("team_name"),
                func.count(MatchParticipation.id).label("matches_played"),
                func.count(case((Match.result == "won", 1))).label("wins"),
                func.count(case((Match.result == "lost", 1))).label("losses"),
                func.count(case((Match.result == "tied", 1))).label("ties"),
                func.count(case((Match.result == "drawn", 1))).label("draws"),
            )
            .join(Match, MatchParticipation.match_id == Match.id)
            .join(Player, MatchParticipation.player_id == Player.id)
            .outerjoin(Team, Match.team_id == Team.id)
            .where(*filters)
            .group_by(MatchParticipation.player_id, Player.name, Team.name)
            .order_by(func.count(MatchParticipation.id).desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "player_id": row.player_id,
                "player_name": row.player_name,
                "team_name": row.team_name,
                "matches_played": row.matches_played,
                "wins": row.wins or 0,
                "losses": row.losses or 0,
                "ties": row.ties or 0,
                "draws": row.draws or 0,
                "win_percentage": round(
                    (row.wins or 0) / (row.matches_played or 1) * 100, 1
                ),
            }
            for row in rows
        ]

    async def get_recent_results(
        self,
        limit: int = 10,
        team_id: UUID | None = None,
        season_id: UUID | None = None,
    ) -> list[dict]:
        filters = [self._base_match_filter(), Match.status == "completed"]
        if team_id:
            filters.append(Match.team_id == team_id)
        if season_id:
            filters.append(Match.season_id == season_id)

        stmt = (
            select(
                Match,
                Team.name.label("team_name"),
                FixtureType.name.label("fixture_type_name"),
            )
            .outerjoin(Team, Match.team_id == Team.id)
            .outerjoin(FixtureType, Match.fixture_type_id == FixtureType.id)
            .where(*filters)
            .order_by(Match.date.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "match_id": m.id,
                "match_date": m.date.isoformat(),
                "team_name": team_name,
                "opponent": m.opponent,
                "venue": m.venue,
                "our_score": m.our_score,
                "opponent_score": m.opponent_score,
                "result": m.result,
                "result_margin": m.result_margin,
                "result_margin_type": m.result_margin_type,
                "fixture_type_name": ft_name,
            }
            for m, team_name, ft_name in rows
        ]
