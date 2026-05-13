# MVP Bank Secure SDLC

`MVP Bank` is a minimal banking loan approval system prepared for Secure SDLC and OWASP Top 10 practical work. The product covers the core business scenario: a client submits a credit application, a manager reviews it, and an administrator audits security-relevant events.

## Implemented MVP

- Web UI: dashboard at `/`
- API UI: Swagger at `/api/docs`
- Authentication: registration, login, token refresh, logout, current profile
- Loan workflow: apply, list, detail view, manager decision, CSV export
- Supporting documents: secure upload with size, MIME, magic-byte, and path validation
- Audit trail: admin-only audit log endpoint with sensitive-field redaction

## Architecture

- Backend: Django 5 + Django Ninja
- Data storage: PostgreSQL or SQLite
- Auth: bcrypt password hashing + JWT access/refresh tokens
- Roles: `CLIENT`, `MANAGER`, `ADMIN`
- Logging: database-backed audit log + application logs to stdout
- Deployment: local Python run or Docker Compose

## API endpoints

1. `POST /api/auth/register`
2. `POST /api/auth/login`
3. `POST /api/auth/refresh`
4. `POST /api/auth/logout`
5. `GET /api/auth/me`
6. `POST /api/loans/apply`
7. `GET /api/loans/`
8. `GET /api/loans/export.csv`
9. `GET /api/loans/{loan_id}`
10. `POST /api/loans/{loan_id}/documents`
11. `PATCH /api/loans/{loan_id}/decision`
12. `GET /api/audit/logs`

## Security mechanisms

- password hashing with `bcrypt`
- JWT validation with issuer, audience, expiry, token type, and revocation checks
- access token revocation and refresh token rotation
- role-based and object-level access control
- input validation through Pydantic schemas
- neutral auth error handling and login throttling
- proxy header trust disabled by default
- secure headers: `nosniff`, `DENY`, referrer policy, HSTS in hardened mode
- audit logging with redaction of passwords, tokens, email, and other sensitive fields
- secure file upload handling with path traversal protection
- CSV export hardening against formula injection
- secrets stored in environment variables and `.env`

## Requirements coverage

- UI present: Swagger UI
- 5+ endpoints: yes
- 3+ DB entities: `users`, `credit_applications`, `audit_logs`, `loan_documents`, `login_throttles`, `revoked_tokens`
- 2+ roles: yes, three roles
- main business scenario implemented: yes
- input validation: yes
- password hashing: yes
- access control: yes
- critical event logging without secret leakage: yes

The seed script creates more than 200 rows for demonstration and testing.

## Local run

### 1. Create environment

Copy `.env.example` to `.env` and set secure values:

```env
SECRET_KEY=replace-with-a-long-random-value
JWT_SECRET=replace-with-a-long-random-value
DB_ENGINE=sqlite
SQLITE_PATH=db.sqlite3
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Install dependencies

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

### 3. Apply migrations and seed data

```bash
python manage.py migrate
python seed.py
```

### 4. Start the server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the web UI or [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs) for Swagger.

## HTTPS local demo

Generate a development certificate and run the HTTPS server:

```bash
python scripts/generate_dev_cert.py
python scripts/run_https.py
```

Open [https://127.0.0.1:7443/api/docs](https://127.0.0.1:7443/api/docs).

## Docker Compose

Use PostgreSQL-backed deployment:

```bash
docker compose up --build
```

After startup the system is available at [http://127.0.0.1:8000/](http://127.0.0.1:8000/), with health check at [http://127.0.0.1:8000/healthz](http://127.0.0.1:8000/healthz).

## Testing and security checks

```bash
python manage.py test
python manage.py check --deploy
bandit -r apps core config
pip-audit -r requirements.txt --progress-spinner off
```

## Seeded users

`seed.py` creates:

- `client@testbank.com`
- `client2@testbank.com`
- `manager@testbank.com`
- `admin@testbank.com`

Passwords come from environment variables or are generated at seed time.

## Project structure

- [`config/settings.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/config/settings.py)
- [`config/urls.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/config/urls.py)
- [`apps/auth_app/api.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/auth_app/api.py)
- [`apps/loans/api.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/loans/api.py)
- [`apps/audit/api.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/audit/api.py)
- [`seed.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/seed.py)
- [`reports/practical_work_6_report.md`](/C:/projects/aitu/isscv/mvp3/mvp_bank/reports/practical_work_6_report.md)
- [`reports/practical_work_6_task2_ai_assisted_report.md`](/C:/projects/aitu/isscv/mvp3/mvp_bank/reports/practical_work_6_task2_ai_assisted_report.md)
- [`reports/practical_work_6_comparison.md`](/C:/projects/aitu/isscv/mvp3/mvp_bank/reports/practical_work_6_comparison.md)

## OWASP analysis summary

The detailed table of risks, fixes, retesting results, AI-assisted report, and comparison matrix are in:

- [`reports/practical_work_6_report.md`](/C:/projects/aitu/isscv/mvp3/mvp_bank/reports/practical_work_6_report.md)
- [`reports/practical_work_6_task2_ai_assisted_report.md`](/C:/projects/aitu/isscv/mvp3/mvp_bank/reports/practical_work_6_task2_ai_assisted_report.md)
- [`reports/practical_work_6_comparison.md`](/C:/projects/aitu/isscv/mvp3/mvp_bank/reports/practical_work_6_comparison.md)
