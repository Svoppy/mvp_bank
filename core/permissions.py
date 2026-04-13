"""
Django Ninja authentication backend and role-based permission helpers.
"""
from ninja.security import HttpBearer
from ninja.errors import HttpError

from core.security import decode_token
from apps.auth_app.models import User


class JWTAuth(HttpBearer):
    """
    Reads 'Authorization: Bearer <token>', validates JWT,
    and returns the active User instance (stored in request.auth).
    """
    openapi_bearerFormat = "JWT"
    openapi_description = (
        "Provide the access token received from /api/auth/login or /api/auth/refresh."
    )

    def authenticate(self, request, token: str):
        payload = decode_token(token)
        if payload is None or payload.get("type") != "access":
            return None
        try:
            user = User.objects.get(pk=int(payload["sub"]), is_active=True)
        except (User.DoesNotExist, ValueError, KeyError):
            return None
        request.auth_token = token
        request.auth_token_payload = payload
        return user


jwt_auth = JWTAuth()


def require_roles(*roles: str):
    """
    Returns a dependency function that raises 403 if the authenticated
    user's role is not in the allowed set.
    """

    def check(request):
        user: User = request.auth
        if user.role not in roles:
            raise HttpError(403, "Forbidden: insufficient permissions")
        return user

    return check


def get_client_user(request) -> User:
    user: User = request.auth
    if user.role != "CLIENT":
        raise HttpError(403, "Forbidden: clients only")
    return user


def get_manager_user(request) -> User:
    user: User = request.auth
    if user.role != "MANAGER":
        raise HttpError(403, "Forbidden: managers only")
    return user


def get_admin_user(request) -> User:
    user: User = request.auth
    if user.role != "ADMIN":
        raise HttpError(403, "Forbidden: admins only")
    return user
