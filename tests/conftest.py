import uuid
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.main import create_app
from app.models.base import Base
from app.schemas.auth import ClubMembership, CurrentUser

TEST_DATABASE_URL = (
    "postgresql+asyncpg://ccm_admin:ccm_local_password@localhost:5433/ccm_test"
)

# Fixed UUIDs for test data
TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_CLUB_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
TEST_MEMBER_ID = uuid.UUID("00000000-0000-0000-0000-000000000100")


def make_test_user(
    user_id: uuid.UUID = TEST_USER_ID,
    club_id: uuid.UUID | None = TEST_CLUB_ID,
    role: str = "clubadmin",
    is_platform_admin: bool = False,
) -> CurrentUser:
    memberships = []
    if club_id:
        memberships.append(
            ClubMembership(club_id=club_id, role=role, member_id=TEST_MEMBER_ID)
        )
    return CurrentUser(
        user_id=user_id,
        email=f"test-{user_id}@example.com",
        is_platform_admin=is_platform_admin,
        memberships=memberships,
    )


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        setup_database, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db():
        yield db_session

    test_user = make_test_user()

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def player_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Client authenticated as a player (non-admin)."""
    app = create_app()

    async def override_get_db():
        yield db_session

    test_user = make_test_user(role="player")

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
