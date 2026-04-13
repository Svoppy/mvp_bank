"""
Audit endpoint:
  GET /audit/logs — ADMIN only, paginated list of all audit records
"""
from typing import List

from ninja import Router, Query
from ninja.errors import HttpError
from django.http import HttpRequest

from apps.audit.models import AuditLog
from apps.audit.schemas import AuditLogOut
from core.schemas import ErrorOut
from core.permissions import jwt_auth, get_admin_user

router = Router(tags=["Audit"], auth=jwt_auth)


@router.get(
    "/logs",
    response={200: List[AuditLogOut], 403: ErrorOut},
    operation_id="listAuditLogs",
    summary="List audit log entries",
    description=(
        "ADMIN-only endpoint that returns paginated audit events for security-sensitive actions. "
        "Sensitive data in details is redacted before storage."
    ),
)
def list_audit_logs(
    request: HttpRequest,
    page: int = Query(default=1, ge=1, description="1-based page number."),
    page_size: int = Query(default=50, ge=1, le=200, description="Maximum number of rows to return."),
):
    """
    Return paginated audit logs. ADMIN role required.
    Logs contain NO passwords, tokens, or raw personal data.
    """
    get_admin_user(request)

    offset = (page - 1) * page_size
    qs = AuditLog.objects.all()[offset: offset + page_size]
    return list(qs)
