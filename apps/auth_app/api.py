"""
Authentication endpoints:
  POST /auth/register  — client self-registration
  POST /auth/login     — issue JWT tokens
  POST /auth/refresh   — rotate refresh token and issue new token pair
  POST /auth/logout    — revoke current token pair
  GET  /auth/me        — current user profile
"""
import logging

from ninja import Router
from ninja.errors import HttpError
from django.http import HttpRequest

from apps.auth_app.models import User, Role
from apps.auth_app.schemas import (
    LoginIn,
    LogoutIn,
    MessageOut,
    RefreshIn,
    RegisterIn,
    TokenOut,
    UserOut,
)
from apps.auth_app.services import (
    is_login_blocked,
    normalize_email,
    register_login_failure,
    reset_login_failures,
    revoke_token,
)
from apps.audit.service import log_action
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    dummy_password_hash,
    hash_password,
    verify_password,
)
from core.permissions import jwt_auth

logger = logging.getLogger(__name__)

router = Router(tags=["Auth"])


@router.post("/register", response={201: UserOut}, auth=None)
def register(request: HttpRequest, data: RegisterIn):
    """Register a new client account."""
    email = normalize_email(data.email)

    if User.objects.filter(email=email).exists():
        # Neutral message — don't reveal whether email exists
        raise HttpError(400, "Registration failed. Please check your data.")

    user = User.objects.create(
        email=email,
        hashed_password=hash_password(data.password),
        role=Role.CLIENT,
        full_name=data.full_name,
    )

    log_action(
        user=user,
        action="USER_REGISTER",
        entity_type="User",
        entity_id=user.pk,
        ip_address=_get_ip(request),
        details={"role": user.role},
    )
    logger.info("New client registered: user_id=%s", user.pk)
    return 201, user


@router.post("/login", response=TokenOut, auth=None)
def login(request: HttpRequest, data: LoginIn):
    """Authenticate and return JWT access + refresh tokens."""
    email = normalize_email(data.email)
    ip_address = _get_ip(request)

    if is_login_blocked(email, ip_address):
        log_action(
            user=None,
            action="LOGIN_BLOCKED",
            ip_address=ip_address,
            details={"reason": "rate_limited"},
        )
        raise HttpError(429, "Too many login attempts. Try again later.")

    # Always run verify_password to prevent timing attacks even on missing user
    user = User.objects.filter(email=email, is_active=True).first()
    stored_hash = user.hashed_password if user else dummy_password_hash()

    if not verify_password(data.password, stored_hash) or user is None:
        register_login_failure(email, ip_address)
        log_action(
            user=user,
            action="LOGIN_FAILED",
            ip_address=ip_address,
            details={"reason": "invalid_credentials"},
        )
        raise HttpError(401, "Invalid credentials")

    reset_login_failures(email, ip_address)
    access = create_access_token(user.pk, user.role)
    refresh = create_refresh_token(user.pk)

    log_action(
        user=user,
        action="LOGIN_SUCCESS",
        ip_address=ip_address,
        details={},
    )
    logger.info("Login success: user_id=%s role=%s", user.pk, user.role)
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/refresh", response=TokenOut, auth=None)
def refresh_tokens(request: HttpRequest, data: RefreshIn):
    """Rotate a refresh token and return a fresh access/refresh pair."""
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HttpError(401, "Invalid token")

    try:
        user = User.objects.get(pk=int(payload["sub"]), is_active=True)
    except (User.DoesNotExist, KeyError, ValueError):
        raise HttpError(401, "Invalid token")

    revoke_token(payload=payload, user=user, reason="refresh_rotated")

    access = create_access_token(user.pk, user.role)
    refresh = create_refresh_token(user.pk)

    log_action(
        user=user,
        action="TOKEN_REFRESH",
        ip_address=_get_ip(request),
        details={},
    )
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/logout", response=MessageOut, auth=jwt_auth)
def logout(request: HttpRequest, data: LogoutIn):
    """Invalidate the current access token and optionally the supplied refresh token."""
    user: User = request.auth
    access_payload = getattr(request, "auth_token_payload", None)

    if isinstance(access_payload, dict):
        revoke_token(payload=access_payload, user=user, reason="logout")

    if data.refresh_token:
        refresh_payload = decode_token(data.refresh_token)
        if (
            isinstance(refresh_payload, dict)
            and refresh_payload.get("type") == "refresh"
            and refresh_payload.get("sub") == str(user.pk)
        ):
            revoke_token(payload=refresh_payload, user=user, reason="logout")

    log_action(
        user=user,
        action="LOGOUT",
        ip_address=_get_ip(request),
        details={},
    )
    return MessageOut(message="Logged out")


@router.get("/me", response=UserOut, auth=jwt_auth)
def me(request: HttpRequest):
    """Return the authenticated user's own profile. No sensitive fields."""
    return request.auth


def _get_ip(request: HttpRequest) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
