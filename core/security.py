"""
Security helpers: password hashing (bcrypt) and JWT token handling.
Passwords are NEVER logged or stored in plaintext.
"""
import os
from functools import lru_cache
from datetime import datetime, timezone, timedelta
from uuid import uuid4

import bcrypt
import jwt

# bcrypt cost factor 12 — strong against brute force, ~300ms per hash
_BCRYPT_ROUNDS = 12

ACCESS_TOKEN_TTL = timedelta(minutes=30)
REFRESH_TOKEN_TTL = timedelta(days=7)


def hash_password(plain: str) -> str:
    """Return bcrypt hash of a plaintext password (encoded, stored as str)."""
    encoded = plain.encode("utf-8")
    hashed = bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=_BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the bcrypt hash. Constant-time comparison."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


@lru_cache(maxsize=1)
def dummy_password_hash() -> str:
    """
    Valid bcrypt hash used to normalize login timing for unknown users.
    Cached to avoid expensive re-hashing on every failed login attempt.
    """
    return hash_password("DummyPassword123!")


def _jwt_secret() -> str:
    secret = os.environ.get("JWT_SECRET", "")
    if not secret:
        raise RuntimeError("JWT_SECRET env var is not set")
    return secret


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + ACCESS_TOKEN_TTL).timestamp()),
        "type": "access",
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int((now + REFRESH_TOKEN_TTL).timestamp()),
        "type": "refresh",
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """
    Decode and validate a JWT. Returns payload dict or None if invalid/expired.
    Never raises — callers treat None as unauthenticated.
    """
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

    token_id = payload.get("jti")
    if token_id is None:
        return None

    from apps.auth_app.services import is_token_revoked

    if is_token_revoked(str(token_id)):
        return None
    return payload
