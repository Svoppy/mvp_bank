# Generated for Practical Work 5 security hardening.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth_app", "0001_initial"),
        ("loans", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LoanDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_name", models.CharField(max_length=120)),
                ("stored_name", models.CharField(max_length=100, unique=True)),
                ("content_type", models.CharField(max_length=100)),
                ("size_bytes", models.PositiveIntegerField()),
                ("sha256", models.CharField(max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "loan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="documents",
                        to="loans.creditapplication",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="uploaded_loan_documents",
                        to="auth_app.user",
                    ),
                ),
            ],
            options={
                "db_table": "loan_documents",
                "indexes": [models.Index(fields=["loan", "created_at"], name="loan_docume_loan_id_82aa4c_idx")],
            },
        ),
    ]
