from uuid import UUID

from pydantic import BaseModel


class ClubMembership(BaseModel):
    club_id: UUID
    role: str
    member_id: UUID | None


class CurrentUser(BaseModel):
    user_id: UUID
    email: str
    is_platform_admin: bool = False
    memberships: list[ClubMembership] = []


class MeResponse(BaseModel):
    user_id: UUID
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    is_platform_admin: bool
    clubs: list[ClubMembership]
