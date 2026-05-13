"""
Test data seeder.
Run: python manage.py shell < seed.py
OR:  python seed.py   (if DJANGO_SETTINGS_MODULE is set)

Passwords are read from environment variables if provided:
  SEED_CLIENT_PASSWORD
  SEED_CLIENT2_PASSWORD
  SEED_MANAGER_PASSWORD
  SEED_ADMIN_PASSWORD

If a variable is absent, a strong password is generated at runtime and printed once.

The practical work requires a realistic dataset. This script creates:
  - 4 users with 3 roles
  - 220 credit applications
  - audit records for registration, login, and loan review events
"""

import os
import secrets
import string
from decimal import Decimal

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.audit.models import AuditLog
from apps.audit.service import log_action
from apps.auth_app.models import Role, User
from apps.loans.models import ApplicationStatus, CreditApplication
from core.security import hash_password

print("Seeding test data...")


def generate_password(length: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    required = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%^&*"),
    ]
    remaining = [secrets.choice(alphabet) for _ in range(max(0, length - len(required)))]
    password_chars = required + remaining
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


users_data = [
    {
        "email": "client@testbank.com",
        "password_env": "SEED_CLIENT_PASSWORD",
        "role": Role.CLIENT,
        "full_name": "Alice Ivanova",
    },
    {
        "email": "client2@testbank.com",
        "password_env": "SEED_CLIENT2_PASSWORD",
        "role": Role.CLIENT,
        "full_name": "Bob Petrov",
    },
    {
        "email": "manager@testbank.com",
        "password_env": "SEED_MANAGER_PASSWORD",
        "role": Role.MANAGER,
        "full_name": "Carol Sidorova",
    },
    {
        "email": "admin@testbank.com",
        "password_env": "SEED_ADMIN_PASSWORD",
        "role": Role.ADMIN,
        "full_name": "Dave Admin",
    },
]

created_users: dict[str, User] = {}
issued_passwords: dict[str, str] = {}
for user_data in users_data:
    password = os.environ.get(user_data["password_env"]) or generate_password()
    user, created = User.objects.update_or_create(
        email=user_data["email"],
        defaults={
            "hashed_password": hash_password(password),
            "role": user_data["role"],
            "full_name": user_data["full_name"],
            "is_active": True,
        },
    )
    created_users[user_data["email"]] = user
    issued_passwords[user_data["email"]] = password
    print(f"  {'Created' if created else 'Updated'} user: {user_data['email']} [{user_data['role']}]")

client_one = created_users["client@testbank.com"]
client_two = created_users["client2@testbank.com"]
manager = created_users["manager@testbank.com"]
admin = created_users["admin@testbank.com"]

purposes = [
    "Home renovation",
    "Car purchase",
    "Business expansion",
    "Medical treatment",
    "Education expenses",
    "Agricultural equipment",
    "Office renovation",
    "Working capital",
    "Travel services expansion",
    "Warehouse modernization",
]

created_loans = 0
updated_loans = 0
all_loans: list[CreditApplication] = []

for index in range(220):
    client = client_one if index % 2 == 0 else client_two
    purpose = f"{purposes[index % len(purposes)]} #{index + 1}"
    amount = Decimal("50000.00") + Decimal(index * 7500)
    term_months = 6 + (index % 60) * 3

    loan, created = CreditApplication.objects.update_or_create(
        client=client,
        purpose=purpose,
        defaults={
            "amount": amount,
            "term_months": term_months,
            "status": ApplicationStatus.PENDING,
            "manager": None,
            "decision_comment": "",
        },
    )
    all_loans.append(loan)
    if created:
        created_loans += 1
    else:
        updated_loans += 1

for index, loan in enumerate(all_loans):
    if index % 5 == 0:
        loan.status = ApplicationStatus.APPROVED
        loan.manager = manager
        loan.decision_comment = "Approved after document and income review."
        loan.save(update_fields=["status", "manager", "decision_comment", "updated_at"])
    elif index % 7 == 0:
        loan.status = ApplicationStatus.REJECTED
        loan.manager = manager
        loan.decision_comment = "Rejected because debt burden exceeded policy threshold."
        loan.save(update_fields=["status", "manager", "decision_comment", "updated_at"])

print(
    "  Credit applications: "
    f"created={created_loans}, updated={updated_loans}, total={CreditApplication.objects.count()}"
)

for user in (client_one, client_two, manager, admin):
    if not AuditLog.objects.filter(action="SEED_USER_READY", user=user).exists():
        log_action(
            user=user,
            action="SEED_USER_READY",
            entity_type="User",
            entity_id=user.pk,
            details={"role": user.role},
        )

for loan in all_loans[:80]:
    if not AuditLog.objects.filter(action="SEED_LOAN_REVIEWED", entity_id=loan.pk).exists():
        log_action(
            user=manager,
            action="SEED_LOAN_REVIEWED",
            entity_type="CreditApplication",
            entity_id=loan.pk,
            details={"status": loan.status, "client_id": loan.client_id},
        )

if not AuditLog.objects.filter(action="SEED_ADMIN_VERIFIED", user=admin).exists():
    log_action(
        user=admin,
        action="SEED_ADMIN_VERIFIED",
        entity_type="AuditLog",
        details={"summary": "Seed dataset verified for secure SDLC practical work."},
    )

print("\nDone! Test accounts:")
print(f"  client@testbank.com   / {issued_passwords['client@testbank.com']}  (CLIENT)")
print(f"  client2@testbank.com  / {issued_passwords['client2@testbank.com']}  (CLIENT)")
print(f"  manager@testbank.com  / {issued_passwords['manager@testbank.com']} (MANAGER)")
print(f"  admin@testbank.com    / {issued_passwords['admin@testbank.com']}  (ADMIN)")
print(f"  Total users: {User.objects.count()}")
print(f"  Total loans: {CreditApplication.objects.count()}")
print(f"  Total audit records: {AuditLog.objects.count()}")
