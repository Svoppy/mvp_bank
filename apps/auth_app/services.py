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


def _scope_targets(email: str, ip_address: str | None) -> list[tuple[str, str | None]]:
    normalized_email = normalize_email(email)
    return [
        (f"email:{normalized_email}", None),
        (f"email_ip:{normalized_email}|{ip_address or 'unknown'}", ip_address),
    ]


def is_login_blocked(email: str, ip_address: str | None) -> bool:
    scope_keys = [scope_key for scope_key, _ in _scope_targets(email, ip_address)]
    now = timezone.now()
    return LoginThrottle.objects.filter(
        scope_key__in=scope_keys,
        blocked_until__gt=now,
    ).exists()


def _update_failure_record(record: LoginThrottle, now) -> None:
    if record.blocked_until and record.blocked_until > now:
        record.last_failure_at = now
        record.save(update_fields=["last_failure_at", "updated_at"])
        return

    window_start = record.first_failure_at or now
    if window_start + LOGIN_WINDOW < now:
        record.failure_count = 0
        record.first_failure_at = now
        record.blocked_until = None

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


@transaction.atomic
def register_login_failure(email: str, ip_address: str | None) -> LoginThrottle:
    now = timezone.now()
    normalized_email = normalize_email(email)
    primary_record: LoginThrottle | None = None

    for scope_key, scope_ip in _scope_targets(normalized_email, ip_address):
        record = LoginThrottle.objects.select_for_update().filter(scope_key=scope_key).first()
        if record is None:
            record = LoginThrottle.objects.create(
                scope_key=scope_key,
                email=normalized_email,
                ip_address=scope_ip,
                failure_count=1,
                first_failure_at=now,
                last_failure_at=now,
            )
        else:
            _update_failure_record(record, now)

        if primary_record is None:
            primary_record = record

    if primary_record is None:
        raise RuntimeError("Login throttle update failed")
    return primary_record


def reset_login_failures(email: str, ip_address: str | None) -> None:
    scope_keys = [scope_key for scope_key, _ in _scope_targets(email, ip_address)]
    LoginThrottle.objects.filter(scope_key__in=scope_keys).delete()


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
) -> bool:
    token_id = payload.get("jti")
    token_type = payload.get("type")
    exp = payload.get("exp")
    if token_id is None or token_type is None or exp is None:
        return False

    try:
        token_uuid = UUID(str(token_id))
    except (TypeError, ValueError):
        return False

    expires_at = datetime.fromtimestamp(int(exp), tz=dt_timezone.utc)

    _, created = RevokedToken.objects.get_or_create(
        jti=token_uuid,
        defaults={
            "user": user,
            "token_type": str(token_type),
            "reason": reason[:50],
            "expires_at": expires_at,
        },
    )
    return created
