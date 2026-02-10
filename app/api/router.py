from fastapi import APIRouter

from app.api.v1 import (
    announcements,
    auth,
    availability,
    clubs,
    fixture_series,
    fixture_types,
    health,
    matches,
    members,
    navigation,
    players,
    platform,
    profiles,
    registration,
    roles,
    seasons,
    selections,
    teams,
)

api_router = APIRouter(prefix="/api/v1")

# Public
api_router.include_router(health.router)

# Auth
api_router.include_router(auth.router)

# Registration (approved-clubs is public, rest require auth)
api_router.include_router(registration.router)
api_router.include_router(registration.club_registrations_router)

# Profiles
api_router.include_router(profiles.router)

# Roles & Permissions
api_router.include_router(roles.router)
api_router.include_router(roles.permissions_router)
api_router.include_router(roles.user_perms_router)
api_router.include_router(roles.members_router)
api_router.include_router(roles.clubs_roles_router)

# Platform admin
api_router.include_router(platform.router)
api_router.include_router(navigation.router)

# Club-scoped resources
api_router.include_router(clubs.router)
api_router.include_router(members.router)
api_router.include_router(seasons.router)
api_router.include_router(teams.router)
api_router.include_router(players.router)
api_router.include_router(matches.router)
api_router.include_router(matches.fixtures_router)
api_router.include_router(availability.router)
api_router.include_router(availability.bulk_router)
api_router.include_router(selections.router)
api_router.include_router(fixture_types.router)
api_router.include_router(fixture_series.router)
api_router.include_router(announcements.router)
