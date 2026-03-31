from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from runtime import get_runtime_config


bearer_scheme = HTTPBearer(auto_error=False)


def create_access_token(identity: str) -> str:
    config = get_runtime_config()
    expires_minutes = int(getattr(config, "JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 15))
    payload = {
        "sub": identity,
        "type": "access",
    }
    if expires_minutes > 0:
        payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    return jwt.encode(payload, str(config.JWT_SECRET_KEY), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, str]:
    config = get_runtime_config()
    try:
        payload = jwt.decode(token, str(config.JWT_SECRET_KEY), algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.") from exc

    token_type = str(payload.get("type", "access"))
    if token_type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")
    return payload


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> int:
    if credentials is None or str(credentials.scheme).lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Header",
        )

    payload = decode_access_token(credentials.credentials)
    identity = payload.get("sub")
    if identity is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    return int(identity)
