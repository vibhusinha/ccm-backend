from uuid import UUID

from pydantic import BaseModel, Field


class PlayCricketSyncRequest(BaseModel):
    season: int = Field(..., ge=2000, le=2100)


class PlayCricketScorecardSyncRequest(BaseModel):
    match_id: UUID


class SyncResult(BaseModel):
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = []


class SyncAllResult(BaseModel):
    teams: SyncResult
    players: SyncResult
    matches: SyncResult
