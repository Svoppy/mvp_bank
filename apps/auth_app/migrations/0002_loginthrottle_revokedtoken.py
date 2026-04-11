import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_app", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LoginThrottle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scope_key", models.CharField(max_length=320, unique=True)),
                ("email", models.EmailField(max_length=254)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("failure_count", models.PositiveSmallIntegerField(default=0)),
                ("first_failure_at", models.DateTimeField(blank=True, null=True)),
                ("last_failure_at", models.DateTimeField(blank=True, null=True)),
                ("blocked_until", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "login_throttles",
            },
        ),
        migrations.CreateModel(
            name="RevokedToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("jti", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("token_type", models.CharField(max_length=10)),
                ("reason", models.CharField(default="logout", max_length=50)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="revoked_tokens",
                        to="auth_app.user",
                    ),
                ),
            ],
            options={
                "db_table": "revoked_tokens",
            },
        ),
        migrations.AddIndex(
            model_name="revokedtoken",
            index=models.Index(fields=["jti"], name="revoked_tok_jti_8c2714_idx"),
        ),
        migrations.AddIndex(
            model_name="revokedtoken",
            index=models.Index(fields=["expires_at"], name="revoked_tok_expires_cdc4fe_idx"),
        ),
    ]
