"""Password hashing and JWT access-token utilities."""

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "30"))

if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is missing.")

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Create a secure Argon2 hash from a plaintext password."""

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    stored_password_hash: str,
) -> bool:
    """Check a plaintext password against its stored Argon2 hash."""

    return password_hash.verify(
        plain_password,
        stored_password_hash,
    )


def create_access_token(user_id: int) -> str:
    """Create a signed JWT identifying one active user."""

    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=JWT_ACCESS_TOKEN_MINUTES)

    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """Validate a JWT and return its decoded claims."""

    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={
            "require": [
                "sub",
                "iat",
                "exp",
            ]
        },
    )
