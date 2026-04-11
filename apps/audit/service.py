"""
Audit logging service — centralised function used by all apps.
NEVER pass passwords, tokens, or secrets in the 'details' dict.
"""
import logging
from collections.abc import Mapping, Sequence

from apps.audit.models import AuditLog
from apps.auth_app.models import User

logger = logging.getLogger(__name__)

_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = {
    "access_token",
    "authorization",
    "cookie",
    "email",
    "full_name",
    "hashed_password",
    "jwt",
    "password",
    "refresh_token",
    "secret",
    "token",
}


def _sanitize_value(value, key: str | None = None):
    if key and key.lower() in _SENSITIVE_KEYS:
        return _REDACTED

    if isinstance(value, Mapping):
        return {
            str(item_key)[:50]: _sanitize_value(item_value, str(item_key))
            for item_key, item_value in value.items()
        }

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_sanitize_value(item) for item in list(value)[:20]]

    if isinstance(value, str):
        return value.strip()[:200]

    return value


def log_action(
    *,
    user: User | None,
    action: str,
    entity_type: str = "",
    entity_id: int | None = None,
    ip_address: str | None = None,
    details: dict | None = None,
) -> None:
    """
    Write an audit record to the database.
    Failures are caught and logged to stderr so they never break the main flow.
    """
    try:
        sanitized_details = _sanitize_value(details or {})
        AuditLog.objects.create(
            user=user,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            ip_address=ip_address,
            details=sanitized_details,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("AuditLog write failed action=%s error=%s", action, exc)
