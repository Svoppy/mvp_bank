import json
import secrets
from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase

from apps.auth_app.models import Role, User
from core.security import hash_password


def strong_test_password() -> str:
    return f"Aa1!{secrets.token_hex(6)}"


class AuthApiTests(TestCase):
    def setUp(self):
        self.client_password = strong_test_password()
        self.client_user = User.objects.create(
            email="client@example.com",
            hashed_password=hash_password(self.client_password),
            role=Role.CLIENT,
            full_name="Client User",
        )

    def test_refresh_rotation_invalidates_old_refresh_token(self):
        login_response = self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "client@example.com", "password": self.client_password}),
            content_type="application/json",
        )

        self.assertEqual(login_response.status_code, 200)
        refresh_token = login_response.json()["refresh_token"]

        refresh_response = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

        self.assertEqual(refresh_response.status_code, 200)

        replay_response = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )

        self.assertEqual(replay_response.status_code, 401)

    def test_logout_revokes_access_and_refresh_tokens(self):
        login_response = self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "client@example.com", "password": self.client_password}),
            content_type="application/json",
        )

        self.assertEqual(login_response.status_code, 200)
        access_token = login_response.json()["access_token"]
        refresh_token = login_response.json()["refresh_token"]

        logout_response = self.client.post(
            "/api/auth/logout",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(logout_response.status_code, 200)

        me_response = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        self.assertEqual(me_response.status_code, 401)

        refresh_response = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": refresh_token}),
            content_type="application/json",
        )
        self.assertEqual(refresh_response.status_code, 401)

    def test_failed_logins_are_rate_limited(self):
        for _ in range(5):
            response = self.client.post(
                "/api/auth/login",
                data=json.dumps({"email": "client@example.com", "password": "Wrong123!"}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 401)

        blocked_response = self.client.post(
            "/api/auth/login",
            data=json.dumps({"email": "client@example.com", "password": "Wrong123!"}),
            content_type="application/json",
        )

        self.assertEqual(blocked_response.status_code, 429)

    @patch("apps.auth_app.api.User.objects.create", side_effect=DatabaseError("db down"))
    def test_register_returns_503_when_database_is_unavailable(self, _mock_create):
        response = self.client.post(
            "/api/auth/register",
            data=json.dumps(
                {
                    "email": "newclient@example.com",
                    "password": "Aa1!ClientPass99",
                    "full_name": "New Client",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)

    def test_swagger_docs_and_openapi_publish_all_mvp_routes(self):
        docs_response = self.client.get("/api/docs")
        self.assertEqual(docs_response.status_code, 200)
        self.assertContains(docs_response, "swagger-ui")

        schema_response = self.client.get("/api/openapi.json")
        self.assertEqual(schema_response.status_code, 200)

        schema = schema_response.json()
        self.assertEqual(schema["info"]["title"], "MVP Bank - Credit Approval API")
        self.assertIn("/api/auth/login", schema["paths"])
        self.assertIn("/api/auth/register", schema["paths"])
        self.assertIn("/api/auth/refresh", schema["paths"])
        self.assertIn("/api/auth/logout", schema["paths"])
        self.assertIn("/api/auth/me", schema["paths"])
        self.assertIn("/api/loans/apply", schema["paths"])
        self.assertIn("/api/loans/", schema["paths"])
        self.assertIn("/api/loans/export.csv", schema["paths"])
        self.assertIn("/api/loans/{loan_id}", schema["paths"])
        self.assertIn("/api/loans/{loan_id}/documents", schema["paths"])
        self.assertIn("/api/loans/{loan_id}/decision", schema["paths"])
        self.assertIn("/api/audit/logs", schema["paths"])

        security_schemes = schema["components"]["securitySchemes"].values()
        self.assertTrue(
            any(item.get("type") == "http" and item.get("scheme") == "bearer" for item in security_schemes)
        )

    def test_root_ui_and_health_endpoint_are_available(self):
        index_response = self.client.get("/")
        self.assertEqual(index_response.status_code, 200)
        self.assertContains(index_response, "MVP Bank")
        self.assertContains(index_response, "Credit approval workflow")

        health_response = self.client.get("/healthz")
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(
            health_response.json(),
            {
                "status": "ok",
                "service": "mvp-bank",
                "api_docs": "/api/docs",
            },
        )
