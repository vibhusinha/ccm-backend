import time
from typing import Any

import httpx
from jose import JWTError, jwt

from app.config import get_settings
from app.core.exceptions import AuthenticationError

settings = get_settings()

_jwks_cache: dict[str, Any] = {}
_jwks_cache_time: float = 0
_JWKS_CACHE_TTL = 3600  # 1 hour


async def _fetch_jwks() -> dict[str, Any]:
    global _jwks_cache, _jwks_cache_time

    if _jwks_cache and (time.time() - _jwks_cache_time) < _JWKS_CACHE_TTL:
        return _jwks_cache

    async with httpx.AsyncClient() as client:
        resp = await client.get(settings.computed_jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cache_time = time.time()
        return _jwks_cache


async def decode_supabase_jwt(token: str) -> dict[str, Any]:
    """Decode and validate a Supabase access token.

    Tries RS256 via JWKS first, falls back to HS256 with JWT secret.
    """
    # Try RS256 via JWKS
    try:
        jwks = await _fetch_jwks()
        unverified_header = jwt.get_unverified_header(token)

        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header.get("kid"):
                rsa_key = key
                break

        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=["RS256"],
                audience="authenticated",
                issuer=f"{settings.supabase_url}/auth/v1",
            )
            return payload
    except (JWTError, httpx.HTTPError):
        pass

    # Fallback: HS256 with JWT secret
    if not settings.supabase_jwt_secret:
        raise AuthenticationError("Invalid token")

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {e}")
