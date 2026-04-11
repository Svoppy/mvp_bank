"""
Loan endpoints:
  POST   /loans/apply             — client submits credit application
  GET    /loans/                  — list applications (client: own; manager: all)
  GET    /loans/{loan_id}         — get single application (object-level auth)
  PATCH  /loans/{loan_id}/decision — manager approve/reject
"""
import logging
from typing import List

from ninja import Router
from ninja.errors import HttpError
from django.http import HttpRequest

from apps.auth_app.models import User
from apps.loans.models import CreditApplication, ApplicationStatus
from apps.loans.schemas import LoanApplyIn, DecisionIn, LoanOut
from apps.audit.service import log_action
from core.permissions import jwt_auth, get_manager_user

logger = logging.getLogger(__name__)

router = Router(tags=["Loans"], auth=jwt_auth)


@router.post("/apply", response={201: LoanOut})
def apply_loan(request: HttpRequest, data: LoanApplyIn):
    """Client submits a new credit application."""
    user: User = request.auth
    if user.role != "CLIENT":
        raise HttpError(403, "Only clients can submit applications")

    loan = CreditApplication.objects.create(
        client=user,
        amount=data.amount,
        term_months=data.term_months,
        purpose=data.purpose,
    )

    log_action(
        user=user,
        action="LOAN_APPLY",
        entity_type="CreditApplication",
        entity_id=loan.pk,
        ip_address=_get_ip(request),
        details={"amount": str(data.amount), "term_months": data.term_months},
    )
    logger.info("Loan application submitted: loan_id=%s client_id=%s", loan.pk, user.pk)
    return 201, loan


@router.get("/", response=List[LoanOut])
def list_loans(request: HttpRequest):
    """
    CLIENT: returns only their own applications.
    MANAGER: returns all applications.
    """
    user: User = request.auth
    if user.role == "CLIENT":
        qs = CreditApplication.objects.filter(client=user).order_by("-created_at")
    elif user.role == "MANAGER":
        qs = CreditApplication.objects.all().order_by("-created_at")
    else:
        raise HttpError(403, "Forbidden: insufficient permissions")
    return list(qs)


@router.get("/{loan_id}", response=LoanOut)
def get_loan(request: HttpRequest, loan_id: int):
    """
    Get a single application.
    Object-level auth: clients can only view their own applications.
    """
    user: User = request.auth
    loan = _get_loan_or_404(loan_id)
    _assert_can_view(user, loan)
    return loan


@router.patch("/{loan_id}/decision", response=LoanOut)
def make_decision(request: HttpRequest, loan_id: int, data: DecisionIn):
    """Manager approves or rejects an application."""
    manager: User = get_manager_user(request)
    loan = _get_loan_or_404(loan_id)

    if loan.status != ApplicationStatus.PENDING:
        raise HttpError(409, "Application has already been decided")

    loan.status = data.status
    loan.manager = manager
    loan.decision_comment = data.comment
    loan.save(update_fields=["status", "manager", "decision_comment", "updated_at"])

    log_action(
        user=manager,
        action=f"LOAN_{data.status}",
        entity_type="CreditApplication",
        entity_id=loan.pk,
        ip_address=_get_ip(request),
        details={"new_status": data.status, "client_id": loan.client_id},
    )
    logger.info(
        "Loan decision: loan_id=%s status=%s manager_id=%s",
        loan.pk, data.status, manager.pk,
    )
    return loan


# ── helpers ──────────────────────────────────────────────────────────────────

def _get_loan_or_404(loan_id: int) -> CreditApplication:
    try:
        return CreditApplication.objects.get(pk=loan_id)
    except CreditApplication.DoesNotExist:
        raise HttpError(404, "Application not found")


def _assert_can_view(user: User, loan: CreditApplication) -> None:
    """Object-level authorization for loan records."""
    if user.role == "MANAGER":
        return

    if user.role == "CLIENT" and loan.client_id != user.pk:
        # Return 404 instead of 403 to avoid information leakage
        raise HttpError(404, "Application not found")

    if user.role != "CLIENT":
        raise HttpError(403, "Forbidden: insufficient permissions")


def _get_ip(request: HttpRequest) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
