import uuid

from django.db import models


class Role(models.TextChoices):
    CLIENT = "CLIENT", "Client"
    MANAGER = "MANAGER", "Manager"
    ADMIN = "ADMIN", "Admin"


class User(models.Model):
    email = models.EmailField(unique=True, max_length=254)
    hashed_password = models.CharField(max_length=200)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)
    full_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.email} ({self.role})"


class LoginThrottle(models.Model):
    scope_key = models.CharField(max_length=320, unique=True)
    email = models.EmailField(max_length=254)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    failure_count = models.PositiveSmallIntegerField(default=0)
    first_failure_at = models.DateTimeField(null=True, blank=True)
    last_failure_at = models.DateTimeField(null=True, blank=True)
    blocked_until = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "login_throttles"

    def __str__(self):
        return f"{self.email} failures={self.failure_count}"


class RevokedToken(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_tokens",
    )
    jti = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_type = models.CharField(max_length=10)
    reason = models.CharField(max_length=50, default="logout")
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "revoked_tokens"
        indexes = [
            models.Index(fields=["jti"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.token_type} token {self.jti}"
