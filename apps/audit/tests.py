from django.test import TestCase
import secrets

from apps.audit.models import AuditLog
from apps.audit.service import log_action
from apps.auth_app.models import Role, User
from core.security import create_access_token, hash_password


def strong_test_password() -> str:
    return f"Aa1!{secrets.token_hex(6)}"


class AuditTests(TestCase):
    def setUp(self):
        admin_password = strong_test_password()
        client_password = strong_test_password()
        self.admin = User.objects.create(
            email="admin@example.com",
            hashed_password=hash_password(admin_password),
            role=Role.ADMIN,
            full_name="Admin User",
        )
        self.client_user = User.objects.create(
            email="client@example.com",
            hashed_password=hash_password(client_password),
            role=Role.CLIENT,
            full_name="Client User",
        )

    def _auth_header(self, user: User) -> str:
        token = create_access_token(user.pk, user.role)
        return f"Bearer {token}"

    def test_audit_service_redacts_sensitive_details(self):
        log_action(
            user=self.admin,
            action="TEST_EVENT",
            details={
                "email": "hidden@example.com",
                "token": "secret-token",
                "nested": {"password": "unsafe", "safe": "ok"},
            },
        )

        log_entry = AuditLog.objects.get(action="TEST_EVENT")
        self.assertEqual(log_entry.details["email"], "[REDACTED]")
        self.assertEqual(log_entry.details["token"], "[REDACTED]")
        self.assertEqual(log_entry.details["nested"]["password"], "[REDACTED]")
        self.assertEqual(log_entry.details["nested"]["safe"], "ok")

    def test_audit_logs_endpoint_is_admin_only(self):
        log_action(user=self.admin, action="ADMIN_LOGIN", details={})

        client_response = self.client.get(
            "/api/audit/logs",
            HTTP_AUTHORIZATION=self._auth_header(self.client_user),
        )
        self.assertEqual(client_response.status_code, 403)

        admin_response = self.client.get(
            "/api/audit/logs",
            HTTP_AUTHORIZATION=self._auth_header(self.admin),
        )
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(len(admin_response.json()), 1)
