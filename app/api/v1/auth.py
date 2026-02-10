from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import decode_access_token
from app.schemas.auth import (
    AuthTokenResponse,
    CurrentUser,
    LoginRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
)
from app.services.auth_service import AuthService
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthTokenResponse:
    """Register a new user with email and password."""
    auth_service = AuthService(db)
    profile, access_token, refresh_token = await auth_service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
    )


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthTokenResponse:
    """Authenticate with email and password."""
    auth_service = AuthService(db)
    profile, access_token, refresh_token = await auth_service.login(
        email=body.email,
        password=body.password,
    )
    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=profile.id,
        email=profile.email,
        full_name=profile.full_name,
    )


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_token(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthTokenResponse:
    """Exchange a refresh token for new access + refresh tokens."""
    auth_service = AuthService(db)
    access_token, new_refresh_token = await auth_service.refresh(body.refresh_token)

    payload = decode_access_token(access_token)

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user_id=UUID(payload["sub"]),
        email=payload["email"],
    )


@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    profile_service = ProfileService(db)
    profile = await profile_service.get_by_id(current_user.user_id)

    return MeResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=profile.full_name if profile else None,
        avatar_url=profile.avatar_url if profile else None,
        is_platform_admin=current_user.is_platform_admin,
        clubs=current_user.memberships,
    )
