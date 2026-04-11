import json
import secrets

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
