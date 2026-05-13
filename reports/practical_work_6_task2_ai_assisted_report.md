# Practical Work 6 - Task 2

## Topic

Development of an AI-assisted version of the product and security analysis of the resulting data flows and implementation.

## Goal

Build a functionally equivalent version of the product with AI assistance, document the AI tools and prompts used, and compare the security posture of AI-assisted development against the baseline MVP.

## AI-assisted version overview

The AI-assisted version preserves the same business scenario:

- client registration and login
- credit application submission
- manager review and decision
- administrator audit review
- document upload and CSV export

The resulting implementation uses the same platform stack:

- Django 5
- Django Ninja
- SQLite / PostgreSQL
- JWT authentication
- bcrypt password hashing
- Docker Compose deployment

## AI tools and models used

- Codex coding agent
- GPT-class model for:
  - architecture refinement
  - security hardening suggestions
  - test generation
  - deployment artifact generation
  - README and report drafting

## Prompt log used during AI-assisted development

1. Build a secure loan approval MVP with Django and role-based access control.
2. Add JWT authentication with refresh-token rotation and revocation support.
3. Protect the API against Broken Access Control and Authentication Failures.
4. Add audit logging without leaking passwords, tokens, or sensitive personal data.
5. Validate uploaded files by MIME type, magic bytes, file size, and safe storage path.
6. Add CSV export protection against formula injection.
7. Harden Django deployment settings according to `check --deploy`.
8. Add a browser dashboard for clients, managers, and administrators.
9. Add Docker deployment artifacts and health checks.
10. Generate test coverage for authentication, authorization, uploads, audit logs, and UI availability.

## Architecture of the AI-assisted version

- browser dashboard at `/`
- HTTP API at `/api/...`
- role model: `CLIENT`, `MANAGER`, `ADMIN`
- audit service for critical events
- token lifecycle service
- loan document storage service
- export service for controlled CSV streaming

## Roles and access boundaries

- `CLIENT`: own loans only, document upload, CSV export of own data
- `MANAGER`: all loans, decision workflow
- `ADMIN`: audit visibility only

## Main business scenario

1. User self-registers as client.
2. Client logs in and obtains JWT tokens.
3. Client creates a loan application.
4. Client uploads supporting documents.
5. Manager reviews and approves/rejects the application.
6. Admin checks the audit trail and security-relevant events.

## Implemented security mechanisms

- password hashing with bcrypt
- strict JWT validation
- token revocation and refresh rotation
- login throttling
- role-based and object-level access control
- schema-based validation
- audit redaction
- secure headers
- upload validation
- CSV sanitization
- deployment hardening

## OWASP Top 10 analysis of the AI-assisted version

| Category | Risk in AI-assisted development | Implemented mitigation |
|---|---|---|
| Broken Access Control | AI may generate over-permissive endpoints | Manual review plus tests for object-level and role-based access |
| Authentication Failures | AI may omit replay protection or throttling | Added refresh rotation, revocation, and login throttling |
| Injection | AI may accept unsafe raw input | Used schema validation and output sanitization |
| Security Misconfiguration | AI may default to insecure debug/dev settings | Hardened settings and `check --deploy` verification |
| Cryptographic Failures | AI may suggest weak token/password handling | Enforced bcrypt and strict JWT claims |
| Insecure Design | AI may conflate business roles | Kept explicit role separation in API design |
| Software/Data Integrity Failures | AI may generate unsafe upload/storage logic | Added allowlist, magic-byte checks, and path containment |
| Logging/Monitoring Failures | AI may log sensitive payloads | Centralized redacting audit logger |
| Software Supply Chain Failures | AI may introduce risky packages | Kept dependency set small and pinned |
| Exceptional Conditions | AI may leak stack traces or internal details | Neutral error handling and controlled `503` behavior |

## Verification results

- `python manage.py test` - passed
- `python manage.py check --deploy` - passed
- `bandit -r apps core config` - no findings
- browser dashboard available at `/`
- local deployment verified on `http://127.0.0.1:8002/`

## Conclusion

AI assistance accelerated implementation and documentation, but security quality still depended on explicit review, targeted test coverage, and manual validation of OWASP-related risks. The strongest result came from combining AI-assisted generation with deliberate hardening and verification.
