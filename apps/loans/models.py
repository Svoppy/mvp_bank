from django.db import models
from apps.auth_app.models import User


class ApplicationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class CreditApplication(models.Model):
    client = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="applications"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    term_months = models.IntegerField()
    purpose = models.TextField(max_length=500)
    status = models.CharField(
        max_length=10,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decisions",
    )
    decision_comment = models.TextField(max_length=1000, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "credit_applications"

    @property
    def client_email(self) -> str:
        return self.client.email

    def __str__(self):
        return f"Application #{self.pk} - {self.status}"


class LoanDocument(models.Model):
    loan = models.ForeignKey(
        CreditApplication,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="uploaded_loan_documents",
    )
    original_name = models.CharField(max_length=120)
    stored_name = models.CharField(max_length=100, unique=True)
    content_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "loan_documents"
        indexes = [
            models.Index(fields=["loan", "created_at"], name="loan_docume_loan_id_82aa4c_idx"),
        ]

    def __str__(self):
        return f"Document #{self.pk} for loan #{self.loan_id}"
