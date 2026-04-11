from datetime import datetime, timedelta, timezone as dt_timezone
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.auth_app.models import LoginThrottle, RevokedToken, User

MAX_LOGIN_FAILURES = 5
LOGIN_WINDOW = timedelta(minutes=15)
LOGIN_BLOCK_DURATION = timedelta(minutes=15)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _scope_key(email: str, ip_address: str | None) -> str:
    return f"{normalize_email(email)}|{ip_address or 'unknown'}"


def is_login_blocked(email: str, ip_address: str | None) -> bool:
    record = LoginThrottle.objects.filter(scope_key=_scope_key(email, ip_address)).first()
    if record is None or record.blocked_until is None:
        return False
    return record.blocked_until > timezone.now()


@transaction.atomic
def register_login_failure(email: str, ip_address: str | None) -> LoginThrottle:
    now = timezone.now()
    email = normalize_email(email)
    scope_key = _scope_key(email, ip_address)
    record = LoginThrottle.objects.select_for_update().filter(scope_key=scope_key).first()

    if record is None:
        return LoginThrottle.objects.create(
            scope_key=scope_key,
            email=email,
            ip_address=ip_address,
            failure_count=1,
            first_failure_at=now,
            last_failure_at=now,
        )

    if record.blocked_until and record.blocked_until > now:
        record.last_failure_at = now
        record.save(update_fields=["last_failure_at", "updated_at"])
        return record

    window_start = record.first_failure_at or now
    if window_start + LOGIN_WINDOW < now:
        record.failure_count = 0
        record.first_failure_at = now

    record.failure_count += 1
    record.last_failure_at = now

    if record.failure_count >= MAX_LOGIN_FAILURES:
        record.blocked_until = now + LOGIN_BLOCK_DURATION

    record.save(
        update_fields=[
            "failure_count",
            "first_failure_at",
            "last_failure_at",
            "blocked_until",
            "updated_at",
        ]
    )
    return record


def reset_login_failures(email: str, ip_address: str | None) -> None:
    LoginThrottle.objects.filter(scope_key=_scope_key(email, ip_address)).delete()


def is_token_revoked(token_id: str) -> bool:
    try:
        token_uuid = UUID(str(token_id))
    except (TypeError, ValueError):
        return True
    return RevokedToken.objects.filter(jti=token_uuid).exists()


def revoke_token(
    *,
    payload: dict,
    user: User | None,
    reason: str,
) -> None:
    token_id = payload.get("jti")
    token_type = payload.get("type")
    exp = payload.get("exp")
    if token_id is None or token_type is None or exp is None:
        return

    try:
        token_uuid = UUID(str(token_id))
    except (TypeError, ValueError):
        return

    expires_at = datetime.fromtimestamp(int(exp), tz=dt_timezone.utc)

    RevokedToken.objects.get_or_create(
        jti=token_uuid,
        defaults={
            "user": user,
            "token_type": str(token_type),
            "reason": reason[:50],
            "expires_at": expires_at,
        },
    )
