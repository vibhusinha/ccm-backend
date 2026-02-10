import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.club import Club
from tests.conftest import TEST_CLUB_ID


@pytest.fixture
async def seed_club(db_session: AsyncSession):
    club = Club(id=TEST_CLUB_ID, name="Test Cricket Club", slug="test-cc")
    db_session.add(club)
    await db_session.flush()
    return club


@pytest.mark.asyncio
async def test_get_club(client: AsyncClient, seed_club):
    response = await client.get(f"/api/v1/clubs/{TEST_CLUB_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Cricket Club"
    assert data["slug"] == "test-cc"


@pytest.mark.asyncio
async def test_update_club(client: AsyncClient, seed_club):
    response = await client.patch(
        f"/api/v1/clubs/{TEST_CLUB_ID}",
        json={"name": "Updated CC"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated CC"


@pytest.mark.asyncio
async def test_get_club_not_found(client: AsyncClient):
    response = await client.get("/api/v1/clubs/00000000-0000-0000-0000-000000000099")
    assert response.status_code == 403
