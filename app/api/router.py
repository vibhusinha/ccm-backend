from fastapi import APIRouter

from app.api.v1 import (
    auth,
    availability,
    clubs,
    fixture_series,
    fixture_types,
    health,
    matches,
    members,
    players,
    seasons,
    selections,
    teams,
)

api_router = APIRouter(prefix="/api/v1")

# Public
api_router.include_router(health.router)

# Auth
api_router.include_router(auth.router)

# Club-scoped resources
api_router.include_router(clubs.router)
api_router.include_router(members.router)
api_router.include_router(seasons.router)
api_router.include_router(teams.router)
api_router.include_router(players.router)
api_router.include_router(matches.router)
api_router.include_router(availability.router)
api_router.include_router(availability.bulk_router)
api_router.include_router(selections.router)
api_router.include_router(fixture_types.router)
api_router.include_router(fixture_series.router)
