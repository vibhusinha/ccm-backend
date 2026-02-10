import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.club import Club
from app.models.club_member import ClubMember
from app.models.profile import Profile
from tests.conftest import TEST_CLUB_ID, TEST_MEMBER_ID, TEST_USER_ID


@pytest.fixture
async def seed_club_and_member(db_session: AsyncSession):
    club = Club(id=TEST_CLUB_ID, name="Test CC", slug="test-cc-members")
    db_session.add(club)

    profile = Profile(id=TEST_USER_ID, email="admin@test.com", full_name="Admin User")
    db_session.add(profile)

    member = ClubMember(
        id=TEST_MEMBER_ID, user_id=TEST_USER_ID, club_id=TEST_CLUB_ID, role="clubadmin"
    )
    db_session.add(member)
    await db_session.flush()
    return club, member


@pytest.mark.asyncio
async def test_list_members(client: AsyncClient, seed_club_and_member):
    response = await client.get(f"/api/v1/clubs/{TEST_CLUB_ID}/members/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_add_member(client: AsyncClient, seed_club_and_member, db_session: AsyncSession):
    new_user_id = uuid.uuid4()
    new_profile = Profile(id=new_user_id, email="newplayer@test.com", full_name="New Player")
    db_session.add(new_profile)
    await db_session.flush()

    response = await client.post(
        f"/api/v1/clubs/{TEST_CLUB_ID}/members/",
        json={"user_id": str(new_user_id), "role": "player"},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "player"
