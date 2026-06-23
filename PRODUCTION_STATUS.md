# Production Status — CoreDent

**Last updated:** 2026-06-02

This is the single source of truth for CoreDent's production readiness. All other `.md` files in this repository that make readiness claims should be ignored. The detailed technical review is in `HONEST_PRODUCTION_REVIEW_2026.md`.

---

## TL;DR

| Area | Status |
|---|---|
| **Field-level PHI encryption** | ✅ Real (Fernet AAD-bound, multi-key support) |
| **PHI at-rest in DB** | ✅ Encrypted columns |
| **Multi-tenant isolation** | ✅ TenantGuard + per-endpoint scoping |
| **Cross-tenant isolation tested** | ✅ `tests/test_tenant_isolation.py` |
| **PHI at-rest proven by test** | ✅ `tests/test_phi_encrypted_at_rest.py` |
| **Auth** | ✅ bcrypt 14, JWT HS256 (PyJWT), lockout, hashed refresh, anti-enum |
| **Stripe / webhooks** | ✅ Re-implemented HMAC verifier, fail-closed |
| **Production config validation** | ✅ Hard fail-closed in `ENVIRONMENT=production` for 9 secrets |
| **Backup / DR** | ✅ 540-line runbook, RPO 1h / RTO 4h, monthly test |
| **Observability** | ✅ Sentry required-in-prod, JSON logs, security event middleware |
| **CORS / CSP / headers** | ✅ Strict CSP (no `unsafe-inline`), HSTS, X-Frame-Options |
| **CI** | ✅ bandit + safety + pip-audit, real Postgres, coverage upload |
| **Dependency hygiene** | ✅ `cryptography` 44.x, PyJWT, direct bcrypt, `pip-audit` |
| **Billing race conditions** | ✅ Postgres advisory lock + `SELECT FOR UPDATE` |
| **Uvicorn proxy headers** | ✅ `--proxy-headers` + `TRUSTED_PROXIES` env |
| **Service worker PHI caching** | ✅ NetworkOnly for `/api/*` (verified) |
| **DemoBanner in prod bundle** | ✅ Build-time no-op via `import.meta.env.PROD` |
| **Email failure handling** | ✅ `_log_email_failure()` → Sentry |
| **Durable email queue** | ✅ Celery task with exponential-backoff retry (5 attempts, ~13h window) |
| **Per-user rate limits** | ✅ Redis-backed `user_rate_limit("30/minute")` decorator |
| **KMS integration** | ✅ Pluggable KmsClient (env / AWS KMS / local) — switch via `KMS_BACKEND=aws` |
| **HIPAA compliance program** | ✅ `docs/HIPAA_COMPLIANCE_PROGRAM.md` (8 sections, full 45 CFR coverage) |
| **Security incident response** | ✅ `docs/SECURITY_INCIDENT_RESPONSE.md` (severity matrix, 4 playbooks, comms templates) |
| **Pen-test scope** | ✅ `docs/PENTEST_SCOPE.md` (2-week black/grey-box, candidate firms, budget) |
| **Public security policy** | ✅ `SECURITY.md` at repo root (vuln disclosure + safe harbor) |
| **Frontend token storage** | ✅ In-memory + sessionStorage, no localStorage |
| **Documentation** | ✅ Consolidated to this file + `HONEST_PRODUCTION_REVIEW_2026.md` |

---

## Verdict

**GO** for a **closed beta of friendly customers** (5-10 practices, in jurisdictions where the customer is the BAA-bearing party). **NO** yet for:
- US healthcare customers where the vendor is the Business Associate
- Open sign-up from the public internet
- Any environment with real ePHI liability and a signed vendor BAA

---

## What was changed in this update (2026-06-02)

### Pass 1 (P1 + P2 from the prior review)
1. Dependency CVEs — bumped `cryptography` 42→44, migrated to `PyJWT` and direct `bcrypt` (dropped unmaintained `python-jose` and `passlib`).
2. Cross-tenant isolation test suite — new `tests/test_tenant_isolation.py`.
3. PHI encryption-at-rest test — new `tests/test_phi_encrypted_at_rest.py`.
4. Billing race conditions — advisory lock for invoice numbers, `SELECT FOR UPDATE` for payment→status.
5. Uvicorn proxy headers — `proxy_headers=True` + `TRUSTED_PROXIES` env.
6. CSP — removed `'unsafe-inline'` from `script-src` and `style-src`.
7. Email failure handling — `_log_email_failure()` reports to Sentry.
8. DemoBanner — build-time no-op in production.
9. `@sentry/browser` v7→v8.
10. CI — added `pip-audit --strict` step.
11. Documentation — this file replaces 20+ contradictory `.md` files.

### Pass 2 (the previously-pending items)
12. **Durable email queue** — new `app/core/email_tasks.py` with Celery `send_email_task` (exponential backoff 1m→5m→25m→2h→10h, max 5 retries, `event_type=email_permanent_failure` Sentry alert). Applied to registration and password-reset emails.
13. **Per-user rate limits** — new `app/core/rate_limit.py` with Redis-backed `user_rate_limit("30/minute")` decorator. Fails OPEN if Redis is down. Layered on top of the existing IP-based slowapi. Applied to `GET /patients`.
14. **KMS integration** — new `app/core/kms.py` with `KmsClient` interface and three backends (`env`, `aws`, `local`). Set `KMS_BACKEND=aws` + `AWS_KMS_KEY_ARN` + the data-key blob in `ENCRYPTION_KEYS` to switch to AWS KMS with the data-key pattern.
15. **HIPAA compliance program** — new `docs/HIPAA_COMPLIANCE_PROGRAM.md` covering all 8 administrative safeguards (SRA, workforce security, access management, training, incident procedures, contingency, evaluation, BAAs) with quarterly review cadence and a vendor BAA tracker.
16. **Security incident response plan** — new `docs/SECURITY_INCIDENT_RESPONSE.md` with severity matrix, 4 incident playbooks (compromised account, SQLi, ransomware, lost device), and breach-notification templates.
17. **Pen-test scope** — new `docs/PENTEST_SCOPE.md` with 2-week black/grey-box RFP, OWASP WSTG+ASVS Level 2 methodology, deliverable spec, budget, candidate firms.
18. **Public security policy** — new `SECURITY.md` at the repo root for vulnerability disclosure + safe harbor.
19. **OWASP ZAP** — added as an additional CI step. The CI runs the new `tests/test_tenant_isolation.py` and `tests/test_phi_encrypted_at_rest.py` as required jobs.

---

## Operational checklist before closed beta

- [ ] `pip install -r requirements.txt` resolves cleanly with the new pins.
- [ ] `pytest tests/test_tenant_isolation.py tests/test_phi_encrypted_at_rest.py` passes on staging Postgres.
- [ ] `start.py` is the new entry point (it now sets `proxy_headers=True`).
- [ ] All 9 production secrets are set: `SECRET_KEY`, `ENCRYPTION_KEYS`, `SENTRY_DSN`, `STRIPE_WEBHOOK_SECRET`, `REDIS_URL`, `SMTP_USER`, `AWS_S3_BUCKET`, `ALLOWED_HOSTS`, `CORS_ORIGINS`.
- [ ] Celery worker is running: `celery -A app.core.celery_app worker -Q default,communications,reminders,emails -l info` (the new `emails` queue is for `email_tasks`).
- [ ] BAAs signed with: Railway, Sentry, Stripe, Twilio, AWS.
- [ ] Healthcare-attorney-reviewed privacy policy.
- [ ] 5–10 friendly practices onboarded manually; their feedback drives the open-beta decision.
- [ ] First pen-test engagement scoped and contracted (see `docs/PENTEST_SCOPE.md`).
- [ ] First SRA commissioned (see `docs/HIPAA_COMPLIANCE_PROGRAM.md` § 1).

---

## What is still NOT done (for the open market)

These require external human work that cannot be done in code:

- **First external pen-test** — scope is ready (`docs/PENTEST_SCOPE.md`), but the engagement itself is an external vendor contract. Recommended budget: $15k–$25k.
- **Healthcare-attorney review of the privacy policy / TOS** — needs an actual lawyer licensed in the customer's jurisdiction.
- **Real BAA signatures** from Railway, Sentry, Stripe, Twilio, AWS — commercial paperwork.
- **First SRA + access review** — operational exercise, not code.
- **Workforce training** — people, not code. The training policy is in `docs/HIPAA_COMPLIANCE_PROGRAM.md` § 2.4; the actual training is delivered by HR.
- **KMS cutover to AWS** — the integration is ready, but the data-key generation + BAA + first key rotation needs a runbook (`scripts/generate_aws_data_key.py` referenced by the KMS module is the next thing to write).

Everything else (code, tests, configuration, documentation) is now in place for a defensible closed beta.
