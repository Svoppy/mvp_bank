"""
Network-related helpers.
"""
from __future__ import annotations

import ipaddress

from django.conf import settings
from django.http import HttpRequest


def _is_valid_ip(value: str | None) -> bool:
    if not value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def _extract_forwarded_ip(value: str | None) -> str | None:
    """
    Returns the first valid IP from X-Forwarded-For chain.
    """
    if not value:
        return None
    for part in value.split(","):
        candidate = part.strip()
        if _is_valid_ip(candidate):
            return candidate
    return None


def get_client_ip(request: HttpRequest) -> str | None:
    """
    Safely resolve client IP.
    By default we do NOT trust proxy headers to prevent spoofing.
    """
    if getattr(settings, "TRUST_PROXY_HEADERS", False):
        forwarded_ip = _extract_forwarded_ip(request.META.get("HTTP_X_FORWARDED_FOR"))
        if forwarded_ip:
            return forwarded_ip

    remote_addr = request.META.get("REMOTE_ADDR")
    if _is_valid_ip(remote_addr):
        return remote_addr
    return None
