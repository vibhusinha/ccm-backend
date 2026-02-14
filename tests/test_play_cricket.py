import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.club import Club
from app.models.match import Match
from app.models.player import Player
from app.models.team import Team
from tests.conftest import TEST_CLUB_ID

SITE_ID = 12345


@pytest.fixture
async def seed_club_with_pc(db_session: AsyncSession):
    club = Club(
        id=TEST_CLUB_ID,
        name="Test CC",
        slug="test-cc-pc",
        play_cricket_id=SITE_ID,
    )
    db_session.add(club)
    await db_session.flush()
    return club


@pytest.fixture
async def seed_club_without_pc(db_session: AsyncSession):
    club = Club(id=TEST_CLUB_ID, name="Test CC", slug="test-cc-nopc")
    db_session.add(club)
    await db_session.flush()
    return club


@pytest.fixture
async def seed_team(db_session: AsyncSession, seed_club_with_pc):
    team = Team(
        id=uuid.uuid4(),
        club_id=TEST_CLUB_ID,
        name="1st XI",
        play_cricket_id=999,
    )
    db_session.add(team)
    await db_session.flush()
    return team


@pytest.fixture
async def seed_match(db_session: AsyncSession, seed_team):
    match = Match(
        id=uuid.uuid4(),
        club_id=TEST_CLUB_ID,
        team_id=seed_team.id,
        date="2025-06-15",
        time="14:00",
        opponent="Rival CC",
        venue="Home",
        type="League",
        status="completed",
        play_cricket_id=5001,
    )
    db_session.add(match)
    await db_session.flush()
    return match


def _mock_settings():
    """Patch settings to include a Play-Cricket API token."""
    from app.config import Settings

    settings = Settings(play_cricket_api_token="test-token-123")
    return patch("app.api.v1.play_cricket.get_settings", return_value=settings)


# ── Sync Teams ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sync_teams_success(client: AsyncClient, seed_club_with_pc):
    mock_client_instance = AsyncMock()
    mock_client_instance.get_teams = AsyncMock(
        return_value=[
            {"id": "100", "team_name": "1st XI", "status": "Active"},
            {"id": "101", "team_name": "2nd XI", "status": "Active"},
        ]
    )
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        _mock_settings(),
        patch(
            "app.api.v1.play_cricket.PlayCricketClient",
            return_value=mock_client_instance,
        ),
    ):
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/teams"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 2
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_sync_teams_updates_existing(
    client: AsyncClient, seed_club_with_pc, seed_team
):
    mock_client_instance = AsyncMock()
    mock_client_instance.get_teams = AsyncMock(
        return_value=[
            {"id": "999", "team_name": "1st XI Updated", "status": "Active"},
        ]
    )
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        _mock_settings(),
        patch(
            "app.api.v1.play_cricket.PlayCricketClient",
            return_value=mock_client_instance,
        ),
    ):
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/teams"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["updated"] == 1
    assert data["created"] == 0


# ── Sync Players ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sync_players_success(client: AsyncClient, seed_club_with_pc):
    mock_client_instance = AsyncMock()
    mock_client_instance.get_players = AsyncMock(
        return_value=[
            {"id": "200", "player_name": "Joe Root"},
            {"id": "201", "player_name": "Ben Stokes"},
        ]
    )
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        _mock_settings(),
        patch(
            "app.api.v1.play_cricket.PlayCricketClient",
            return_value=mock_client_instance,
        ),
    ):
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/players",
            json={"season": 2025},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 2
    assert data["errors"] == []


# ── Sync Matches ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sync_matches_success(client: AsyncClient, seed_club_with_pc, seed_team):
    mock_client_instance = AsyncMock()
    mock_client_instance.get_matches = AsyncMock(
        return_value=[
            {
                "id": "300",
                "match_date": "15/06/2025",
                "match_time": "13:00",
                "home_club_id": str(SITE_ID),
                "home_team_id": "999",
                "away_club_name": "Rival CC",
                "ground_name": "Village Green",
                "competition_type": "League",
            },
        ]
    )
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        _mock_settings(),
        patch(
            "app.api.v1.play_cricket.PlayCricketClient",
            return_value=mock_client_instance,
        ),
    ):
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/matches",
            json={"season": 2025},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 1
    assert data["errors"] == []


# ── Sync All ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sync_all_success(client: AsyncClient, seed_club_with_pc):
    mock_client_instance = AsyncMock()
    mock_client_instance.get_teams = AsyncMock(
        return_value=[{"id": "100", "team_name": "1st XI", "status": "Active"}]
    )
    mock_client_instance.get_players = AsyncMock(
        return_value=[{"id": "200", "player_name": "Joe Root"}]
    )
    mock_client_instance.get_matches = AsyncMock(return_value=[])
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        _mock_settings(),
        patch(
            "app.api.v1.play_cricket.PlayCricketClient",
            return_value=mock_client_instance,
        ),
    ):
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/all",
            json={"season": 2025},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["teams"]["created"] == 1
    assert data["players"]["created"] == 1
    assert data["matches"]["created"] == 0


# ── Error Cases ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sync_without_play_cricket_id(client: AsyncClient, seed_club_without_pc):
    with _mock_settings():
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/teams"
        )
    assert response.status_code == 400
    assert "play_cricket_id" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_sync_without_api_token(client: AsyncClient, seed_club_with_pc):
    from app.config import Settings

    settings = Settings(play_cricket_api_token="")
    with patch("app.api.v1.play_cricket.get_settings", return_value=settings):
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/teams"
        )
    assert response.status_code == 400
    assert "token" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_sync_scorecard_match_not_found(client: AsyncClient, seed_club_with_pc):
    fake_match_id = str(uuid.uuid4())
    with _mock_settings():
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/scorecard",
            json={"match_id": fake_match_id},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_sync_players_invalid_season(client: AsyncClient, seed_club_with_pc):
    with _mock_settings():
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/players",
            json={"season": 1999},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_sync_teams_api_error(client: AsyncClient, seed_club_with_pc):
    mock_client_instance = AsyncMock()
    mock_client_instance.get_teams = AsyncMock(
        side_effect=Exception("Connection refused")
    )
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        _mock_settings(),
        patch(
            "app.api.v1.play_cricket.PlayCricketClient",
            return_value=mock_client_instance,
        ),
    ):
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/teams"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["created"] == 0
    assert len(data["errors"]) == 1
    assert "Connection refused" in data["errors"][0]


@pytest.mark.asyncio
async def test_sync_scorecard_success(client: AsyncClient, seed_match):
    mock_client_instance = AsyncMock()
    mock_client_instance.get_match_detail = AsyncMock(
        return_value={
            "home_club_id": str(SITE_ID),
            "home_team_id": "999",
            "away_team_id": "888",
            "result_description": "Won by 5 wickets",
            "toss": "Bat",
            "batted_first": "999",
            "toss_won_by_team_id": "999",
            "innings": [
                {
                    "team_batting_id": "999",
                    "innings_number": "1",
                    "runs": "200",
                    "wickets": "8",
                    "overs": "50",
                    "extra_byes": "2",
                    "extra_leg_byes": "1",
                    "extra_wides": "3",
                    "extra_no_balls": "0",
                    "extra_penalty_runs": "0",
                    "declared": "false",
                    "bat": [
                        {
                            "position": "1",
                            "batsman_name": "Test Player",
                            "batsman_id": "200",
                            "runs": "50",
                            "balls": "60",
                            "fours": "6",
                            "sixes": "1",
                            "how_out": "Caught",
                        }
                    ],
                    "bowl": [
                        {
                            "bowler_name": "Opp Bowler",
                            "bowler_id": None,
                            "overs": "10",
                            "maidens": "2",
                            "runs": "35",
                            "wickets": "2",
                            "wides": "1",
                            "no_balls": "0",
                        }
                    ],
                },
            ],
        }
    )
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=False)

    with (
        _mock_settings(),
        patch(
            "app.api.v1.play_cricket.PlayCricketClient",
            return_value=mock_client_instance,
        ),
    ):
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/play-cricket/sync/scorecard",
            json={"match_id": str(seed_match.id)},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["created"] >= 1
    assert data["errors"] == []
