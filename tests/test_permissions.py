import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.main import create_app
from app.models.club import Club
from app.models.team import Team
from tests.conftest import TEST_CLUB_ID, make_test_user


async def _make_client_with_role(
    db_session: AsyncSession, role: str
) -> AsyncClient:
    app = create_app()

    async def override_get_db():
        yield db_session

    test_user = make_test_user(role=role)

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
async def seed_club(db_session: AsyncSession):
    club = Club(id=TEST_CLUB_ID, name="Perm Test CC", slug="perm-test-cc")
    db_session.add(club)
    await db_session.flush()
    return club


@pytest.mark.asyncio
async def test_player_cannot_create_team(db_session: AsyncSession, seed_club):
    async with await _make_client_with_role(db_session, "player") as client:
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/teams/",
            json={"name": "3rd XI"},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_team(db_session: AsyncSession, seed_club):
    async with await _make_client_with_role(db_session, "clubadmin") as client:
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/teams/",
            json={"name": "3rd XI"},
        )
        assert response.status_code == 201


@pytest.mark.asyncio
async def test_sponsor_cannot_create_match(db_session: AsyncSession, seed_club):
    # Create a team first as admin
    team = Team(id=uuid.uuid4(), club_id=TEST_CLUB_ID, name="1st XI")
    db_session.add(team)
    await db_session.flush()

    async with await _make_client_with_role(db_session, "sponsor") as client:
        response = await client.post(
            f"/api/v1/clubs/{TEST_CLUB_ID}/matches/",
            json={
                "team_id": str(team.id),
                "date": "2026-07-01",
                "time": "14:00:00",
                "opponent": "Test CC",
                "venue": "Home",
                "type": "Friendly",
            },
        )
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_non_member_cannot_access_club(db_session: AsyncSession, seed_club):
    app = create_app()

    async def override_get_db():
        yield db_session

    # User with no club memberships
    test_user = make_test_user(club_id=None)

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/api/v1/clubs/{TEST_CLUB_ID}")
        assert response.status_code == 403
