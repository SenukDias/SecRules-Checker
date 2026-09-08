from __future__ import annotations

from dataclasses import dataclass, field

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JOSEError

from app.config import get_settings

settings = get_settings()
_bearer = HTTPBearer(auto_error=False)

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"

_jwks_cache: dict | None = None


@dataclass
class CurrentUser:
    sub: str
    username: str
    roles: list[str] = field(default_factory=list)

    def has_role(self, *roles: str) -> bool:
        return any(r in self.roles for r in roles)


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.keycloak_jwks_url, timeout=5)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> CurrentUser:
    if settings.auth_disabled:
        # Local/dev-only bypass - never enable in an environment reachable by others.
        return CurrentUser(sub="local-dev", username="local-dev", roles=[ROLE_ADMIN, ROLE_ANALYST, ROLE_VIEWER])

    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k["kid"] == header["kid"]), None)
        if key is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown signing key")

        claims = jwt.decode(
            token,
            key,
            algorithms=[header["alg"]],
            audience=settings.keycloak_client_id,
            issuer=settings.keycloak_issuer,
            options={"verify_aud": False},
        )
    except JOSEError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Invalid token: {exc}") from exc

    realm_roles = claims.get("realm_access", {}).get("roles", [])
    return CurrentUser(sub=claims["sub"], username=claims.get("preferred_username", claims["sub"]), roles=realm_roles)


def require_roles(*roles: str):
    async def _checker(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_role(*roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return _checker
