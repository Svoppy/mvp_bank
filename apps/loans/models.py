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

    def __str__(self):
        return f"Application #{self.pk} — {self.status}"
