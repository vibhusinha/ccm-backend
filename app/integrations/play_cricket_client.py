from __future__ import annotations

from typing import Any

import httpx


class PlayCricketAPIError(Exception):
    def __init__(self, status_code: int, detail: str = "Play-Cricket API error"):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{detail} (HTTP {status_code})")


class PlayCricketClient:
    def __init__(self, base_url: str, api_token: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "PlayCricketClient":
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not self._client:
            raise RuntimeError("Client not initialised. Use 'async with' context manager.")
        params = params or {}
        params["api_token"] = self.api_token
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = await self._client.get(url, params=params)
        if response.status_code != 200:
            raise PlayCricketAPIError(response.status_code, response.text[:500])
        return response.json()

    async def get_teams(self, site_id: int) -> list[dict[str, Any]]:
        data = await self._get(f"sites/{site_id}/teams.json")
        return data.get("teams", [])

    async def get_players(self, site_id: int, season: int) -> list[dict[str, Any]]:
        data = await self._get(f"sites/{site_id}/players.json", {"season": season})
        return data.get("players", [])

    async def get_matches(self, site_id: int, season: int) -> list[dict[str, Any]]:
        data = await self._get("matches.json", {"site_id": site_id, "season": season})
        return data.get("matches", [])

    async def get_match_detail(self, site_id: int, match_id: int) -> dict[str, Any]:
        data = await self._get(
            "result_summary.json", {"site_id": site_id, "match_id": match_id}
        )
        results = data.get("result_summary", [])
        if not results:
            raise PlayCricketAPIError(404, f"No result found for match {match_id}")
        return results[0]
