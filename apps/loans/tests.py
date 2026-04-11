import json
import secrets
from decimal import Decimal

from django.test import TestCase

from apps.auth_app.models import Role, User
from apps.loans.models import ApplicationStatus, CreditApplication
from core.security import create_access_token, hash_password


def strong_test_password() -> str:
    return f"Aa1!{secrets.token_hex(6)}"


class LoanApiTests(TestCase):
    def setUp(self):
        client_password = strong_test_password()
        manager_password = strong_test_password()
        admin_password = strong_test_password()
        self.client_one = User.objects.create(
            email="client1@example.com",
            hashed_password=hash_password(client_password),
            role=Role.CLIENT,
            full_name="Client One",
        )
        self.client_two = User.objects.create(
            email="client2@example.com",
            hashed_password=hash_password(client_password),
            role=Role.CLIENT,
            full_name="Client Two",
        )
        self.manager = User.objects.create(
            email="manager@example.com",
            hashed_password=hash_password(manager_password),
            role=Role.MANAGER,
            full_name="Manager User",
        )
        self.admin = User.objects.create(
            email="admin@example.com",
            hashed_password=hash_password(admin_password),
            role=Role.ADMIN,
            full_name="Admin User",
        )

        self.loan_one = CreditApplication.objects.create(
            client=self.client_one,
            amount=Decimal("250000.00"),
            term_months=24,
            purpose="Home renovation",
        )
        self.loan_two = CreditApplication.objects.create(
            client=self.client_two,
            amount=Decimal("180000.00"),
            term_months=18,
            purpose="Car repair",
        )

    def _auth_header(self, user: User) -> str:
        token = create_access_token(user.pk, user.role)
        return f"Bearer {token}"

    def test_client_can_view_only_own_application(self):
        own_response = self.client.get(
            f"/api/loans/{self.loan_one.pk}",
            HTTP_AUTHORIZATION=self._auth_header(self.client_one),
        )
        self.assertEqual(own_response.status_code, 200)

        foreign_response = self.client.get(
            f"/api/loans/{self.loan_two.pk}",
            HTTP_AUTHORIZATION=self._auth_header(self.client_one),
        )
        self.assertEqual(foreign_response.status_code, 404)

    def test_manager_can_decide_and_api_hides_internal_fields(self):
        response = self.client.patch(
            f"/api/loans/{self.loan_one.pk}/decision",
            data=json.dumps({"status": "APPROVED", "comment": "Stable income"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self._auth_header(self.manager),
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], ApplicationStatus.APPROVED)
        self.assertNotIn("client_id", payload)
        self.assertNotIn("manager_id", payload)
        self.assertNotIn("decision_comment", payload)

        self.loan_one.refresh_from_db()
        self.assertEqual(self.loan_one.manager_id, self.manager.pk)
        self.assertEqual(self.loan_one.decision_comment, "Stable income")

    def test_admin_cannot_access_manager_loan_endpoints(self):
        list_response = self.client.get(
            "/api/loans/",
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(list_response.status_code, 403)

        detail_response = self.client.get(
            f"/api/loans/{self.loan_one.pk}",
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(detail_response.status_code, 403)

        decision_response = self.client.patch(
            f"/api/loans/{self.loan_one.pk}/decision",
            data=json.dumps({"status": "APPROVED", "comment": "Denied for admin"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(decision_response.status_code, 403)
