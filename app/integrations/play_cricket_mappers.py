from __future__ import annotations

"""Pure mapping functions: Play-Cricket API data → CCM model kwargs.

Play-Cricket API field reference (from official v2 docs):
  Teams:  id, team_name, status
  Players: id, player_name, ...
  Matches: id, match_date, match_time, home_team_name, home_team_id,
           away_team_name, away_team_id, home_club_name, home_club_id,
           away_club_name, away_club_id, ground_name, competition_type,
           match_type, status, result, result_description
  Match detail innings: team_batting_name, team_batting_id, innings_number,
           runs, wickets, overs, declared, extra_byes, extra_leg_byes,
           extra_wides, extra_no_balls, extra_penalty_runs, total_extras
  Batting (bat): position, batsman_name, batsman_id, how_out,
           fielder_name, bowler_name, runs, fours, sixes, balls
  Bowling (bowl): bowler_name, bowler_id, overs, maidens, runs,
           wides, wickets, no_balls
"""

from datetime import date, time
from decimal import Decimal
from typing import Any
from uuid import UUID


def map_team(pc_team: dict[str, Any], club_id: UUID) -> dict[str, Any]:
    return {
        "club_id": club_id,
        "name": pc_team.get("team_name", "Unknown"),
        "play_cricket_id": int(pc_team["id"]),
        "is_active": pc_team.get("status", "").lower() != "inactive",
    }


def map_player(pc_player: dict[str, Any], club_id: UUID) -> dict[str, Any]:
    name = pc_player.get("player_name", "")
    if not name:
        first = pc_player.get("first_name", "")
        last = pc_player.get("last_name", "")
        name = f"{first} {last}".strip() or "Unknown"

    return {
        "club_id": club_id,
        "name": name,
        "play_cricket_id": int(pc_player["id"]),
        "role": "All-rounder",  # default; Play-Cricket doesn't expose role cleanly
    }


def _parse_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    # Play-Cricket uses dd/mm/yyyy format
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            from datetime import datetime as dt

            return dt.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _parse_time(time_str: str | None) -> time:
    if not time_str:
        return time(14, 0)
    try:
        parts = time_str.strip().split(":")
        return time(int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
    except (ValueError, IndexError):
        return time(14, 0)


def _determine_venue(
    pc_match: dict[str, Any], site_id: int
) -> str:
    home_club_id = pc_match.get("home_club_id")
    if home_club_id is not None:
        try:
            return "Home" if int(home_club_id) == site_id else "Away"
        except (ValueError, TypeError):
            pass
    return "Home"


def _determine_opponent(pc_match: dict[str, Any], site_id: int) -> str:
    home_club_id = pc_match.get("home_club_id")
    try:
        if home_club_id is not None and int(home_club_id) == site_id:
            return (
                pc_match.get("away_club_name")
                or pc_match.get("away_team_name")
                or "Unknown"
            )
    except (ValueError, TypeError):
        pass
    return (
        pc_match.get("home_club_name")
        or pc_match.get("home_team_name")
        or "Unknown"
    )


def _determine_match_type(pc_match: dict[str, Any]) -> str:
    comp_type = (pc_match.get("competition_type") or "").lower()
    match_type = (pc_match.get("match_type") or "").lower()
    if "friendly" in comp_type:
        return "Friendly"
    if "t20" in match_type or "twenty" in match_type:
        return "T20"
    if "league" in comp_type or "cup" in comp_type:
        return "League"
    return "League"


def _determine_team_id(
    pc_match: dict[str, Any],
    site_id: int,
    team_lookup: dict[int, UUID],
) -> UUID | None:
    home_club_id = pc_match.get("home_club_id")
    try:
        if home_club_id is not None and int(home_club_id) == site_id:
            team_pc_id = pc_match.get("home_team_id")
        else:
            team_pc_id = pc_match.get("away_team_id")
    except (ValueError, TypeError):
        team_pc_id = pc_match.get("home_team_id")

    if team_pc_id is not None:
        try:
            return team_lookup.get(int(team_pc_id))
        except (ValueError, TypeError):
            pass
    return None


def map_match(
    pc_match: dict[str, Any],
    club_id: UUID,
    site_id: int,
    team_lookup: dict[int, UUID],
) -> dict[str, Any]:
    match_date = _parse_date(pc_match.get("match_date"))
    if not match_date:
        match_date = date.today()

    result_desc = pc_match.get("result_description", "")
    pc_result = pc_match.get("result", "")

    status = "upcoming"
    result = None
    if pc_result or result_desc:
        status = "completed"
        result = result_desc or pc_result

    return {
        "club_id": club_id,
        "play_cricket_id": int(pc_match["id"]),
        "date": match_date,
        "time": _parse_time(pc_match.get("match_time")),
        "opponent": _determine_opponent(pc_match, site_id),
        "venue": _determine_venue(pc_match, site_id),
        "type": _determine_match_type(pc_match),
        "status": status,
        "team_id": _determine_team_id(pc_match, site_id, team_lookup),
        "result": result,
        "location_name": pc_match.get("ground_name"),
    }


def map_innings(
    pc_innings: dict[str, Any],
    match_id: UUID,
    home_team_id: int | None,
) -> dict[str, Any]:
    batting_team_id = pc_innings.get("team_batting_id")
    batting_team = "home"
    if batting_team_id is not None and home_team_id is not None:
        try:
            batting_team = "home" if int(batting_team_id) == home_team_id else "opposition"
        except (ValueError, TypeError):
            pass

    overs_str = pc_innings.get("overs", "0")
    try:
        total_overs = Decimal(str(overs_str))
    except Exception:
        total_overs = Decimal("0")

    return {
        "match_id": match_id,
        "innings_number": int(pc_innings.get("innings_number", 1)),
        "batting_team": batting_team,
        "total_runs": int(pc_innings.get("runs", 0)),
        "total_wickets": int(pc_innings.get("wickets", 0)),
        "total_overs": total_overs,
        "extras_byes": int(pc_innings.get("extra_byes", 0)),
        "extras_leg_byes": int(pc_innings.get("extra_leg_byes", 0)),
        "extras_wides": int(pc_innings.get("extra_wides", 0)),
        "extras_no_balls": int(pc_innings.get("extra_no_balls", 0)),
        "extras_penalty": int(pc_innings.get("extra_penalty_runs", 0)),
        "declared": str(pc_innings.get("declared", "")).lower() in ("true", "yes", "1"),
        "all_out": False,
    }


def map_batting_entry(pc_bat: dict[str, Any], innings_id: UUID) -> dict[str, Any]:
    runs = int(pc_bat.get("runs", 0))
    balls = int(pc_bat.get("balls", 0))
    strike_rate = Decimal("0.00")
    if balls > 0:
        strike_rate = Decimal(str(round(runs / balls * 100, 2)))

    how_out = pc_bat.get("how_out", "")
    not_out = how_out.lower() in ("not out", "did not bat", "retired not out", "")

    return {
        "innings_id": innings_id,
        "batting_position": int(pc_bat.get("position", 0)) or None,
        "runs_scored": runs,
        "balls_faced": balls,
        "fours": int(pc_bat.get("fours", 0)),
        "sixes": int(pc_bat.get("sixes", 0)),
        "how_out": how_out or None,
        "not_out": not_out,
        "strike_rate": strike_rate,
        # batsman_name and batsman_id handled by caller for player resolution
    }


def map_bowling_entry(pc_bowl: dict[str, Any], innings_id: UUID) -> dict[str, Any]:
    overs_str = pc_bowl.get("overs", "0")
    try:
        overs = Decimal(str(overs_str))
    except Exception:
        overs = Decimal("0")

    runs_conceded = int(pc_bowl.get("runs", 0))
    economy = Decimal("0.00")
    if overs > 0:
        economy = Decimal(str(round(float(runs_conceded) / float(overs), 2)))

    return {
        "innings_id": innings_id,
        "bowling_position": None,
        "overs_bowled": overs,
        "maidens": int(pc_bowl.get("maidens", 0)),
        "runs_conceded": runs_conceded,
        "wickets_taken": int(pc_bowl.get("wickets", 0)),
        "wides": int(pc_bowl.get("wides", 0)),
        "no_balls": int(pc_bowl.get("no_balls", 0)),
        "economy": economy,
        # bowler_name and bowler_id handled by caller for player resolution
    }
