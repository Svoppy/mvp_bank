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
"""
import os
import secrets
import string

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.auth_app.models import User, Role
from apps.loans.models import CreditApplication
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

# ── Users ────────────────────────────────────────────────────────────────────
users_data = [
    {"email": "client@testbank.com", "password_env": "SEED_CLIENT_PASSWORD", "role": Role.CLIENT, "full_name": "Alice Ivanova"},
    {"email": "client2@testbank.com", "password_env": "SEED_CLIENT2_PASSWORD", "role": Role.CLIENT, "full_name": "Bob Petrov"},
    {"email": "manager@testbank.com", "password_env": "SEED_MANAGER_PASSWORD", "role": Role.MANAGER, "full_name": "Carol Sidorova"},
    {"email": "admin@testbank.com", "password_env": "SEED_ADMIN_PASSWORD", "role": Role.ADMIN, "full_name": "Dave Admin"},
]

created_users = {}
issued_passwords = {}
for ud in users_data:
    password = os.environ.get(ud["password_env"]) or generate_password()
    user, created = User.objects.update_or_create(
        email=ud["email"],
        defaults={
            "hashed_password": hash_password(password),
            "role": ud["role"],
            "full_name": ud["full_name"],
        },
    )
    created_users[ud["email"]] = user
    issued_passwords[ud["email"]] = password
    print(f"  {'Created' if created else 'Updated'} user: {ud['email']} [{ud['role']}]")

# ── Credit Applications ───────────────────────────────────────────────────────
client1 = created_users["client@testbank.com"]
client2 = created_users["client2@testbank.com"]
manager = created_users["manager@testbank.com"]

apps_data = [
    {"client": client1, "amount": "250000.00", "term_months": 36, "purpose": "Home renovation"},
    {"client": client1, "amount": "50000.00",  "term_months": 12, "purpose": "Car purchase"},
    {"client": client2, "amount": "1000000.00","term_months": 120,"purpose": "Business expansion"},
]

loans = []
for ad in apps_data:
    loan, created = CreditApplication.objects.get_or_create(
        client=ad["client"],
        amount=ad["amount"],
        term_months=ad["term_months"],
        defaults={"purpose": ad["purpose"]},
    )
    loans.append(loan)
    print(f"  {'Created' if created else 'Exists '} loan #{loan.pk}: {ad['amount']} / {ad['term_months']}m")

# Approve first loan, reject second
if loans[0].status == "PENDING":
    loans[0].status = "APPROVED"
    loans[0].manager = manager
    loans[0].decision_comment = "Good credit history, approved."
    loans[0].save()
    print(f"  Approved loan #{loans[0].pk}")

if loans[1].status == "PENDING":
    loans[1].status = "REJECTED"
    loans[1].manager = manager
    loans[1].decision_comment = "Insufficient income documentation."
    loans[1].save()
    print(f"  Rejected loan #{loans[1].pk}")

print("\nDone! Test accounts:")
print(f"  client@testbank.com   / {issued_passwords['client@testbank.com']}  (CLIENT)")
print(f"  client2@testbank.com  / {issued_passwords['client2@testbank.com']}  (CLIENT)")
print(f"  manager@testbank.com  / {issued_passwords['manager@testbank.com']} (MANAGER)")
print(f"  admin@testbank.com    / {issued_passwords['admin@testbank.com']}  (ADMIN)")
