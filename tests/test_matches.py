import uuid
from datetime import date, time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.club import Club
from app.models.match import Match
from app.models.team import Team
from tests.conftest import TEST_CLUB_ID


@pytest.fixture
async def seed_match_data(db_session: AsyncSession):
    club = Club(id=TEST_CLUB_ID, name="Test CC", slug="test-cc-matches")
    db_session.add(club)

    team_id = uuid.uuid4()
    team = Team(id=team_id, club_id=TEST_CLUB_ID, name="1st XI")
    db_session.add(team)

    match_id = uuid.uuid4()
    match = Match(
        id=match_id,
        club_id=TEST_CLUB_ID,
        team_id=team_id,
        date=date(2026, 6, 15),
        time=time(14, 0),
        opponent="Rival CC",
        venue="Home",
        type="League",
        status="upcoming",
    )
    db_session.add(match)
    await db_session.flush()
    return {"club": club, "team": team, "match": match}


@pytest.mark.asyncio
async def test_list_matches(client: AsyncClient, seed_match_data):
    response = await client.get(f"/api/v1/clubs/{TEST_CLUB_ID}/matches/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_create_match(client: AsyncClient, seed_match_data):
    team_id = str(seed_match_data["team"].id)
    response = await client.post(
        f"/api/v1/clubs/{TEST_CLUB_ID}/matches/",
        json={
            "team_id": team_id,
            "date": "2026-07-01",
            "time": "14:00:00",
            "opponent": "New Opponent CC",
            "venue": "Away",
            "type": "Friendly",
        },
    )
    assert response.status_code == 201
    assert response.json()["opponent"] == "New Opponent CC"


@pytest.mark.asyncio
async def test_get_upcoming_matches(client: AsyncClient, seed_match_data):
    response = await client.get(f"/api/v1/clubs/{TEST_CLUB_ID}/matches/upcoming")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_cancel_match(client: AsyncClient, seed_match_data):
    match_id = str(seed_match_data["match"].id)
    response = await client.post(
        f"/api/v1/clubs/{TEST_CLUB_ID}/matches/{match_id}/cancel"
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
