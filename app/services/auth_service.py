import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.profile import Profile
from app.models.refresh_token import RefreshToken

settings = get_settings()


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self, email: str, password: str, full_name: str | None = None
    ) -> tuple[Profile, str, str]:
        """Register a new user. Returns (profile, access_token, refresh_token)."""
        result = await self.db.execute(
            select(Profile).where(Profile.email == email.lower().strip())
        )
        if result.scalar_one_or_none():
            raise ConflictError("Email already registered")

        profile = Profile(
            id=uuid.uuid4(),
            email=email.lower().strip(),
            full_name=full_name,
            password_hash=hash_password(password),
            email_verified=False,
        )
        self.db.add(profile)
        await self.db.flush()

        access_token = create_access_token(profile.id, profile.email)
        refresh_token = create_refresh_token()

        rt = RefreshToken(
            user_id=profile.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
        self.db.add(rt)
        await self.db.flush()

        return profile, access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[Profile, str, str]:
        """Authenticate with email/password. Returns (profile, access_token, refresh_token)."""
        result = await self.db.execute(
            select(Profile).where(Profile.email == email.lower().strip())
        )
        profile = result.scalar_one_or_none()

        if not profile or not profile.password_hash:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, profile.password_hash):
            raise AuthenticationError("Invalid email or password")

        access_token = create_access_token(profile.id, profile.email)
        refresh_token = create_refresh_token()

        rt = RefreshToken(
            user_id=profile.id,
            token_hash=hash_token(refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
        self.db.add(rt)
        await self.db.flush()

        return profile, access_token, refresh_token

    async def refresh(self, refresh_token_str: str) -> tuple[str, str]:
        """Exchange a refresh token for new tokens. Returns (access_token, new_refresh_token)."""
        token_hash_val = hash_token(refresh_token_str)

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash_val,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        rt = result.scalar_one_or_none()
        if not rt:
            raise AuthenticationError("Invalid or expired refresh token")

        # Revoke the used refresh token (token rotation)
        rt.revoked = True

        user_result = await self.db.execute(
            select(Profile).where(Profile.id == rt.user_id)
        )
        profile = user_result.scalar_one_or_none()
        if not profile:
            raise AuthenticationError("User not found")

        access_token = create_access_token(profile.id, profile.email)
        new_refresh_token = create_refresh_token()

        new_rt = RefreshToken(
            user_id=profile.id,
            token_hash=hash_token(new_refresh_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.refresh_token_expire_days),
        )
        self.db.add(new_rt)
        await self.db.flush()

        return access_token, new_refresh_token
