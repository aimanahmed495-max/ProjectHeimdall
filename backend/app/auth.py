"""Authentication routes and current-user dependency."""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import get_db
from .rate_limit import login_rate_limiter
from .security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

bearer_scheme = HTTPBearer(auto_error=False)


def user_registration_enabled() -> bool:
    """Return whether public user registration is enabled."""

    return os.getenv(
        "ENABLE_USER_REGISTRATION",
        "true",
    ).lower() in {"1", "true", "yes", "on"}


def authentication_error() -> HTTPException:
    """Create the standard response for failed authentication."""

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Return the active user represented by a valid bearer token."""

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise authentication_error()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise authentication_error()

    user = db.scalar(
        select(models.User).where(
            models.User.user_id == user_id,
            models.User.is_active.is_(True),
            models.User.deleted_at.is_(None),
        )
    )

    if user is None:
        raise authentication_error()

    return user


@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """Create an active user with an Argon2 password hash."""

    if not user_registration_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User registration is disabled.",
        )

    user = models.User(
        username=user_data.username.lower(),
        password_hash=hash_password(user_data.password),
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this username already exists.",
        )

    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=schemas.TokenResponse,
)
def login_user(
    login_data: schemas.UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """Validate credentials and return a signed access token."""

    ip = request.client.host if request.client else "unknown"
    username = login_data.username.lower()
    retry_seconds = login_rate_limiter.retry_after(ip, username)
    if retry_seconds is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(retry_seconds)},
        )

    user = db.scalar(
        select(models.User).where(
            models.User.username == username,
            models.User.is_active.is_(True),
            models.User.deleted_at.is_(None),
        )
    )

    if user is None or not verify_password(
        login_data.password,
        user.password_hash,
    ):
        login_rate_limiter.record_failure(ip, username)
        raise authentication_error()

    login_rate_limiter.record_success(ip, username)
    return schemas.TokenResponse(
        access_token=create_access_token(user.user_id),
    )


@router.get(
    "/me",
    response_model=schemas.UserRead,
)
def get_authenticated_user(
    current_user: models.User = Depends(get_current_user),
):
    """Return the user represented by the bearer token."""

    return current_user
