import uuid
from datetime import date, time
from decimal import Decimal

from app.integrations.play_cricket_mappers import (
    map_batting_entry,
    map_bowling_entry,
    map_innings,
    map_match,
    map_player,
    map_team,
)

CLUB_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
MATCH_ID = uuid.UUID("00000000-0000-0000-0000-000000000020")
INNINGS_ID = uuid.UUID("00000000-0000-0000-0000-000000000030")
TEAM_UUID = uuid.UUID("00000000-0000-0000-0000-000000000040")
SITE_ID = 12345


# ── Teams ──────────────────────────────────────────────────────────────

class TestMapTeam:
    def test_basic_mapping(self):
        result = map_team({"id": "100", "team_name": "1st XI", "status": "Active"}, CLUB_ID)
        assert result["club_id"] == CLUB_ID
        assert result["name"] == "1st XI"
        assert result["play_cricket_id"] == 100
        assert result["is_active"] is True

    def test_inactive_team(self):
        result = map_team({"id": "101", "team_name": "Colts", "status": "Inactive"}, CLUB_ID)
        assert result["is_active"] is False

    def test_missing_name_defaults(self):
        result = map_team({"id": "102"}, CLUB_ID)
        assert result["name"] == "Unknown"

    def test_missing_status_defaults_active(self):
        result = map_team({"id": "103", "team_name": "2nd XI"}, CLUB_ID)
        assert result["is_active"] is True


# ── Players ────────────────────────────────────────────────────────────

class TestMapPlayer:
    def test_basic_mapping(self):
        result = map_player({"id": "200", "player_name": "Joe Root"}, CLUB_ID)
        assert result["club_id"] == CLUB_ID
        assert result["name"] == "Joe Root"
        assert result["play_cricket_id"] == 200
        assert result["role"] == "All-rounder"

    def test_first_last_name_fallback(self):
        result = map_player({"id": "201", "first_name": "Ben", "last_name": "Stokes"}, CLUB_ID)
        assert result["name"] == "Ben Stokes"

    def test_missing_name_defaults(self):
        result = map_player({"id": "202"}, CLUB_ID)
        assert result["name"] == "Unknown"


# ── Matches ────────────────────────────────────────────────────────────

class TestMapMatch:
    def _team_lookup(self):
        return {999: TEAM_UUID}

    def test_basic_home_match(self):
        pc_match = {
            "id": "300",
            "match_date": "15/06/2025",
            "match_time": "13:00",
            "home_club_id": str(SITE_ID),
            "home_club_name": "Our Club",
            "away_club_name": "Rival CC",
            "home_team_id": "999",
            "ground_name": "Village Green",
            "competition_type": "League",
            "result_description": "Won by 5 wickets",
        }
        result = map_match(pc_match, CLUB_ID, SITE_ID, self._team_lookup())
        assert result["club_id"] == CLUB_ID
        assert result["play_cricket_id"] == 300
        assert result["date"] == date(2025, 6, 15)
        assert result["time"] == time(13, 0)
        assert result["opponent"] == "Rival CC"
        assert result["venue"] == "Home"
        assert result["type"] == "League"
        assert result["status"] == "completed"
        assert result["result"] == "Won by 5 wickets"
        assert result["team_id"] == TEAM_UUID
        assert result["location_name"] == "Village Green"

    def test_away_match(self):
        pc_match = {
            "id": "301",
            "match_date": "2025-07-20",
            "home_club_id": "99999",
            "home_club_name": "Away Club",
            "away_club_name": "Our Club",
        }
        result = map_match(pc_match, CLUB_ID, SITE_ID, {})
        assert result["venue"] == "Away"
        assert result["opponent"] == "Away Club"

    def test_upcoming_match(self):
        pc_match = {"id": "302", "match_date": "01/09/2025"}
        result = map_match(pc_match, CLUB_ID, SITE_ID, {})
        assert result["status"] == "upcoming"
        assert result["result"] is None

    def test_friendly_match_type(self):
        pc_match = {"id": "303", "competition_type": "Friendly"}
        result = map_match(pc_match, CLUB_ID, SITE_ID, {})
        assert result["type"] == "Friendly"

    def test_t20_match_type(self):
        pc_match = {"id": "304", "match_type": "T20"}
        result = map_match(pc_match, CLUB_ID, SITE_ID, {})
        assert result["type"] == "T20"

    def test_missing_date_defaults_today(self):
        pc_match = {"id": "305"}
        result = map_match(pc_match, CLUB_ID, SITE_ID, {})
        assert result["date"] == date.today()

    def test_missing_time_defaults_1400(self):
        pc_match = {"id": "306", "match_date": "01/07/2025"}
        result = map_match(pc_match, CLUB_ID, SITE_ID, {})
        assert result["time"] == time(14, 0)

    def test_iso_date_format(self):
        pc_match = {"id": "307", "match_date": "2025-08-15"}
        result = map_match(pc_match, CLUB_ID, SITE_ID, {})
        assert result["date"] == date(2025, 8, 15)


# ── Innings ────────────────────────────────────────────────────────────

class TestMapInnings:
    def test_home_batting(self):
        pc_innings = {
            "team_batting_id": "500",
            "innings_number": "1",
            "runs": "245",
            "wickets": "8",
            "overs": "50",
            "extra_byes": "3",
            "extra_leg_byes": "2",
            "extra_wides": "5",
            "extra_no_balls": "1",
            "extra_penalty_runs": "0",
            "declared": "false",
        }
        result = map_innings(pc_innings, MATCH_ID, 500)
        assert result["match_id"] == MATCH_ID
        assert result["innings_number"] == 1
        assert result["batting_team"] == "home"
        assert result["total_runs"] == 245
        assert result["total_wickets"] == 8
        assert result["total_overs"] == Decimal("50")
        assert result["extras_byes"] == 3
        assert result["extras_leg_byes"] == 2
        assert result["extras_wides"] == 5
        assert result["extras_no_balls"] == 1
        assert result["extras_penalty"] == 0
        assert result["declared"] is False
        assert result["all_out"] is False

    def test_opposition_batting(self):
        pc_innings = {"team_batting_id": "600", "innings_number": "2"}
        result = map_innings(pc_innings, MATCH_ID, 500)
        assert result["batting_team"] == "opposition"

    def test_declared_innings(self):
        pc_innings = {"team_batting_id": "500", "declared": "true"}
        result = map_innings(pc_innings, MATCH_ID, 500)
        assert result["declared"] is True

    def test_no_home_team_defaults_home(self):
        pc_innings = {"team_batting_id": "500"}
        result = map_innings(pc_innings, MATCH_ID, None)
        assert result["batting_team"] == "home"


# ── Batting Entries ────────────────────────────────────────────────────

class TestMapBattingEntry:
    def test_basic_batting(self):
        pc_bat = {
            "position": "3",
            "runs": "75",
            "balls": "100",
            "fours": "8",
            "sixes": "2",
            "how_out": "Caught",
        }
        result = map_batting_entry(pc_bat, INNINGS_ID)
        assert result["innings_id"] == INNINGS_ID
        assert result["batting_position"] == 3
        assert result["runs_scored"] == 75
        assert result["balls_faced"] == 100
        assert result["fours"] == 8
        assert result["sixes"] == 2
        assert result["how_out"] == "Caught"
        assert result["not_out"] is False
        assert result["strike_rate"] == Decimal("75.0")

    def test_not_out(self):
        pc_bat = {"runs": "45", "balls": "30", "how_out": "not out"}
        result = map_batting_entry(pc_bat, INNINGS_ID)
        assert result["not_out"] is True

    def test_did_not_bat(self):
        pc_bat = {"runs": "0", "balls": "0", "how_out": "did not bat"}
        result = map_batting_entry(pc_bat, INNINGS_ID)
        assert result["not_out"] is True

    def test_zero_balls_no_division_error(self):
        pc_bat = {"runs": "10", "balls": "0"}
        result = map_batting_entry(pc_bat, INNINGS_ID)
        assert result["strike_rate"] == Decimal("0.00")

    def test_empty_how_out(self):
        pc_bat = {"runs": "0", "balls": "0", "how_out": ""}
        result = map_batting_entry(pc_bat, INNINGS_ID)
        assert result["how_out"] is None
        assert result["not_out"] is True


# ── Bowling Entries ────────────────────────────────────────────────────

class TestMapBowlingEntry:
    def test_basic_bowling(self):
        pc_bowl = {
            "overs": "10",
            "maidens": "2",
            "runs": "35",
            "wickets": "3",
            "wides": "1",
            "no_balls": "0",
        }
        result = map_bowling_entry(pc_bowl, INNINGS_ID)
        assert result["innings_id"] == INNINGS_ID
        assert result["overs_bowled"] == Decimal("10")
        assert result["maidens"] == 2
        assert result["runs_conceded"] == 35
        assert result["wickets_taken"] == 3
        assert result["wides"] == 1
        assert result["no_balls"] == 0
        assert result["economy"] == Decimal("3.5")

    def test_zero_overs_no_division_error(self):
        pc_bowl = {"overs": "0", "runs": "0"}
        result = map_bowling_entry(pc_bowl, INNINGS_ID)
        assert result["economy"] == Decimal("0.00")

    def test_decimal_overs(self):
        pc_bowl = {"overs": "4.3", "runs": "22", "wickets": "1"}
        result = map_bowling_entry(pc_bowl, INNINGS_ID)
        assert result["overs_bowled"] == Decimal("4.3")
