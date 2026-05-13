# Practical Work 6 Report

## Topic

Development and security assessment of an MVP product according to Secure SDLC and OWASP Top 10.

## Goal

Build and harden a complete MVP product, perform security analysis, fix weaknesses, and confirm remediation with repeat testing.

## Variant

Credit approval and audit system: `MVP Bank`.

## Brief MVP description

`MVP Bank` is a loan-processing system with three roles:

- `CLIENT` registers, logs in, submits loan applications, views only own records, uploads supporting documents, and exports own data.
- `MANAGER` reviews all applications and approves or rejects pending applications.
- `ADMIN` reads the audit trail and monitors security-relevant events.

The system exposes a browser dashboard at `/`, a documented HTTP API with Swagger UI, persists data in SQLite/PostgreSQL, uses JWT authentication, and logs critical actions in an audit table.

## Architecture

- Presentation layer: browser dashboard at `/` and Swagger UI at `/api/docs`
- API layer: Django Ninja routers for `auth`, `loans`, `audit`
- Security layer: JWT auth backend, password hashing, login throttling, token revocation
- Data layer: Django ORM models for `User`, `CreditApplication`, `LoanDocument`, `AuditLog`, `LoginThrottle`, `RevokedToken`
- Storage: PostgreSQL in Docker deployment or SQLite in local demo mode
- File storage: `MEDIA_ROOT/loan_documents/<loan_id>/...`

## Roles and access control

- `CLIENT`
  - allowed: register, login, refresh, logout, me, apply for loans, upload documents to own loans, list/view/export own loans
  - denied: audit logs, manager decisions, access to other clients' loans
- `MANAGER`
  - allowed: login, me, list/view/export all loans, approve/reject pending loans
  - denied: audit logs, creating client applications
- `ADMIN`
  - allowed: login, me, read audit logs
  - denied: client and manager business actions

Object-level authorization is enforced for loan detail access. Foreign loan access for clients returns `404` to avoid record enumeration.

## Main business scenario

1. Client registers and authenticates.
2. Client submits a credit application.
3. Client uploads a supporting document.
4. Manager reviews the pending application.
5. Manager approves or rejects the application.
6. Administrator reviews the audit trail for login attempts, decisions, uploads, and other critical actions.

## Implemented security mechanisms

- bcrypt password hashing
- JWT with issuer, audience, expiry, type, and revocation checks
- refresh token rotation and logout revocation
- login throttling after repeated failures
- input validation through Pydantic schemas
- role-based and object-level access control
- secure headers and hardened deployment settings
- secret management via environment variables and `.env`
- audit logging with sensitive-field redaction
- secure file upload validation
- CSV export sanitization against formula injection
- exception handling that avoids leaking internal details
- pinned dependency versions in `requirements.txt`

## OWASP Top 10 analysis

| OWASP category | Place found | Vulnerability / weakness | Possible impact | Severity | Fix |
|---|---|---|---|---|---|
| Broken Access Control | [`apps/loans/api.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/loans/api.py) | Risk of horizontal access to another client's loan data | Disclosure of applications and decisions | High | Added object-level authorization and `404` on foreign access; admin is explicitly denied from loan routes |
| Authentication Failures | [`apps/auth_app/api.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/auth_app/api.py), [`apps/auth_app/services.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/auth_app/services.py) | Risk of brute force and token replay | Account compromise and session abuse | High | Added login throttling, refresh token rotation, revoked token store, and logout revocation |
| Injection | [`apps/auth_app/schemas.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/auth_app/schemas.py), [`apps/loans/schemas.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/loans/schemas.py) | Unsanitized input could reach logs, exports, or UI | Data corruption, stored payloads, export abuse | Medium | Added schema validation, length limits, and rejection of HTML-like input in text fields |
| Security Misconfiguration | [`config/settings.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/config/settings.py) | Insecure defaults around proxy trust, cookies, headers, and transport | Header spoofing, cookie leakage, TLS downgrade | High | Hardened headers, secure-cookie settings for non-debug mode, HSTS, and disabled proxy trust by default |
| Cryptographic Failures | [`core/security.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/core/security.py) | Weak password storage or incomplete token validation would expose accounts | Credential theft or forged tokens | High | bcrypt hashing, strict JWT validation, secret separation, and expiry enforcement |
| Insecure Design | Router and role model boundaries | Audit, client, and manager workflows could overlap | Excess privileges and weak separation of duties | Medium | Explicit role separation and dedicated admin-only audit API |
| Software or Data Integrity Failures | [`apps/loans/documents.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/loans/documents.py) | Uploaded files could bypass content checks or escape storage path | Malicious files, data tampering, path traversal | High | Enforced MIME allowlist, magic-byte checks, bounded size, safe filename cleaning, and path containment under `MEDIA_ROOT` |
| Security Logging and Alerting Failures | [`apps/audit/service.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/audit/service.py) | Logs could contain tokens, passwords, or personal data | Sensitive data leakage through logs | High | Centralized audit service with redaction of secret and PII-like fields |
| Software Supply Chain Failures | [`requirements.txt`](/C:/projects/aitu/isscv/mvp3/mvp_bank/requirements.txt) | Unpinned or vulnerable packages increase compromise risk | Exploitation via third-party dependencies | Medium | Pinned dependencies and documented `bandit` / `pip-audit` checks |
| Mishandling of Exceptional Conditions | [`apps/auth_app/api.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/apps/auth_app/api.py), [`core/security.py`](/C:/projects/aitu/isscv/mvp3/mvp_bank/core/security.py) | Raw stack traces or detailed auth errors could leak internals | Information disclosure, easier attack preparation | Medium | Neutral errors for invalid credentials, safe `None` on token decode failures, and `503` on database failure |

## Results of repeated testing

### Functional and security verification

- `python manage.py test`
  - result: `14` tests passed
- `python manage.py check --deploy`
  - result: no Django deployment issues reported

### Confirmed security behaviors

- client cannot read another client's application
- admin cannot use manager-only loan endpoints
- refresh token replay is rejected
- logout revokes both access and refresh tokens
- repeated failed logins are throttled
- upload rejects oversized files
- CSV export neutralizes formula-like cells
- audit log redacts sensitive details

## Data volume and entities

The project contains more than three entities and the seeding process creates more than 200 rows:

- `users`
- `credit_applications`
- `loan_documents`
- `audit_logs`
- `login_throttles`
- `revoked_tokens`

`seed.py` creates `220` credit applications plus users and audit records.

## Deployment

- local Python launch supported
- local HTTPS demo supported
- Docker Compose deployment supported through [`docker-compose.yml`](/C:/projects/aitu/isscv/mvp3/mvp_bank/docker-compose.yml)

## Conclusion

The MVP is implemented as a complete applied system with UI, API, storage, role model, authentication, authorization, and security logging. The main business workflow is complete. The identified OWASP-related weaknesses were addressed in code and configuration, and repeat testing confirmed the expected protections.

## Task 2 scaffold

For the AI-assisted implementation, document:

- AI tools and models used
- prompts that influenced architecture, code, and security mechanisms
- equivalent OWASP analysis table
- comparison table with at least 10 criteria against Task 1

Suggested comparison criteria:

1. architecture clarity
2. amount of generated code
3. security by design
4. authentication quality
5. access control quality
6. input validation quality
7. logging quality
8. dependency hygiene
9. exception handling
10. testing depth
11. maintainability
12. time to deliver
