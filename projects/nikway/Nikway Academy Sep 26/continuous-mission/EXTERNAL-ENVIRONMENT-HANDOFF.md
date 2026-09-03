# NIKWAY External Environment Handoff

تاریخ سند: ۳ سپتامبر ۲۰۲۶
وضعیت Mission: `ACTIVE_WITH_EXTERNAL_DEPENDENCIES`
وضعیت Release: `blocked_for_production`

این سند مرجع تحویل محیط برای اتصال‌های واقعی NIKWAY است. هیچ credential، secret یا مقدار محرمانه‌ای در این سند قرار نمی‌گیرد. مقادیر باید از Secret Manager یا CI Secrets تزریق شوند.

## A. Current Readiness

| Gate | وضعیت فعلی | Evidence / مرجع |
|---|---|---|
| Architecture | `PASS_LOCAL` | `publish-ready-sample/V1_MODULE_BOUNDARIES.md` |
| Security | `PASS_LOCAL` | `publish-ready-sample/trivy-local-report-2026-09-03.json` |
| Database | `PARTIAL` | `publish-ready-sample/evidence/runtime-integration-2026-09-03.yaml` |
| RLS | `PASS_LOCAL` | `publish-ready-sample/evidence/rls-full-verification-2026-09-02.yaml` |
| Authorization | `PARTIAL` | `publish-ready-sample/app/app/auth.py` |
| OIDC | `BLOCKED_EXTERNAL` | `publish-ready-sample/app/tests/test_auth.py` |
| S3 | `BLOCKED_EXTERNAL` | `publish-ready-sample/app/tests/test_s3_client.py` |
| Transactions | `PASS_LOCAL` | `publish-ready-sample/app/tests/test_traceability.py` |
| Idempotency | `PASS_LOCAL` | `publish-ready-sample/app/tests/test_audit_event_persistence.py` |
| Audit | `PASS_LOCAL` | `publish-ready-sample/app/tests/test_audit_event_persistence.py` |
| Events | `PASS_LOCAL` | `publish-ready-sample/app/tests/test_traceability.py` |
| API | `PASS_LOCAL` | `publish-ready-sample/generated-openapi.json` |
| E2E | `BLOCKED_EXTERNAL` | `publish-ready-sample/evidence/runtime-integration-2026-09-03.yaml` |
| CI Security | `NOT_RUN` | `.github/workflows/security-scan.yml` |
| Rollback | `PASS_LOCAL` | `publish-ready-sample/app/tests/test_s3_client.py` |
| Evidence | `PASS_LOCAL` | `continuous-mission/evidence/production-readiness-cycle-2026-09-03-006.yaml` |

`PASS_LOCAL` به معنی تأیید staging یا production نیست.

## B. Exact External Inputs Required

### CI Security

- دسترسی به GitHub Actions runner
- اجرای workflow: `.github/workflows/security-scan.yml`
- Threshold: `CRITICAL,HIGH`
- خروجی مورد انتظار: `trivy-fs-report.json`
- Artifact مورد انتظار: `nikway-trivy-filesystem-report`
- مدت نگهداری artifact: ۳۰ روز

### OIDC / JWKS

نام متغیرها:

- `OIDC_ISSUER_URL`
- `OIDC_AUDIENCE`
- `OIDC_JWKS_URL`
- credentialهای test-only برای کاربران معتبر، نامعتبر، منقضی، سازمان اشتباه و role اشتباه

### S3-Compatible Storage

نام متغیرها:

- `S3_ENDPOINT_URL`
- `S3_BUCKET`
- `AWS_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

دسترسی باید scoped و محدود به bucket اختصاصی NIKWAY باشد.

### PostgreSQL Staging

- `DATABASE_URL`
- نام database staging
- host یا endpoint قابل دسترسی از شبکه‌ی application
- runtime role غیرمالک و غیر superuser
- secret مربوط به runtime role فقط از secret manager

## C. Environment Variable Contract

هیچ‌یک از مقدارهای زیر نباید در Git، evidence یا log ذخیره شوند:

```text
DATABASE_URL
OIDC_ISSUER_URL
OIDC_AUDIENCE
OIDC_JWKS_URL
S3_ENDPOINT_URL
S3_BUCKET
AWS_REGION
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

## D. Verification Procedures

### 1. CI Security

1. workflow را در GitHub Actions اجرا کن.
2. commit SHA، run ID، timestamp و conclusion را ثبت کن.
3. artifact `nikway-trivy-filesystem-report` را نگه دار.
4. اگر threshold بدون finding عبور کرد، gate برابر `PASS_STAGING` است.
5. بدون workflow result، gate برابر `NOT_RUN` باقی می‌ماند.

### 2. PostgreSQL Staging

1. secretها را inject کن؛ مقدارشان را چاپ نکن.
2. schema `publish-ready-sample/db/v1_schema.sql` را اعمال کن.
3. owner، superuser و grants runtime role را بررسی کن.
4. procedure موجود را اجرا کن:

```powershell
python -m pytest tests/test_postgres_repository_integration.py tests/test_persistence.py tests/test_audit_event_persistence.py tests/test_progression_trace.py -q
```

5. اتصال، migration، persistence، transaction، rollback، RLS، isolation و privilege boundary را ثبت کن.
6. فقط با evidence staging، gate را `PASS_STAGING` کن.

### 3. OIDC / JWKS

با provider واقعی این موارد را اجرا کن:

- issuer و audience validation
- JWKS retrieval و signature validation
- expiration
- invalid و missing token rejection
- protected endpoint
- organization mapping
- role mapping
- key rotation در صورت پشتیبانی provider

```powershell
python -m pytest tests/test_auth.py tests/test_protected_endpoints.py -q
```

نتیجه‌ی موفق واقعی: `OIDC = PASS_STAGING`.

### 4. S3

1. endpoint، bucket و credential را از secret manager inject کن.
2. اتصال را بررسی کن.
3. upload، checksum، organizational object key و metadata را بررسی کن.
4. read، failure، cleanup، rollback و duplicate request را اجرا کن.

```powershell
python -m pytest tests/test_s3_client.py tests/test_storage.py tests/test_evidence_persistence.py -q
```

MinIO محلی فقط `PASS_LOCAL` است و جایگزین staging واقعی نیست.

### 5. Real Staging E2E

فقط پس از `PASS_STAGING` شدن PostgreSQL، OIDC و S3 اجرا شود:

```text
authentication
→ user resolution
→ organization resolution
→ authorization
→ transaction
→ database persistence
→ object upload
→ event
→ audit
→ idempotency
→ RLS isolation
→ failure handling
→ rollback
→ cleanup
```

نتیجه‌ی موفق واقعی: `E2E = PASS_STAGING`.

## E. Expected PASS Criteria

| Dependency | معیار قبولی |
|---|---|
| CI | Workflow موفق، artifact موجود، threshold بدون CRITICAL/HIGH |
| PostgreSQL | runtime role غیرمالک، غیر superuser، حداقل دسترسی، همه‌ی تست‌های staging موفق |
| OIDC | تمام validationهای هویت و mapping با provider واقعی موفق |
| S3 | upload تا cleanup و rollback با endpoint واقعی موفق |
| E2E | مسیر کامل کاربر و failure path در staging موفق |

## F. Expected Evidence Artifact

هر اجرای واقعی باید شامل این فیلدها باشد:

```text
timestamp
environment
gate
action
result
commit SHA
artifact
operator/source
blocker if any
```

Evidenceهای پیشنهادی:

- `evidence/ci-security-staging-<date>.yaml`
- `evidence/postgres-staging-<date>.yaml`
- `evidence/oidc-staging-<date>.yaml`
- `evidence/s3-staging-<date>.yaml`
- `evidence/e2e-staging-<date>.yaml`

## G. Owner / Source

| Dependency | Owner / Source | وضعیت فعلی | اقدام بعد |
|---|---|---|---|
| CI | Repository / CI owner | `NOT_RUN` | اجرای workflow |
| PostgreSQL | Infrastructure owner | `BLOCKED_EXTERNAL` | تحویل staging endpoint و runtime role |
| OIDC | Environment owner | `BLOCKED_EXTERNAL` | تحویل provider configuration و test credentials |
| S3 | Infrastructure owner | `BLOCKED_EXTERNAL` | تحویل endpoint، bucket و scoped access |
| E2E | Environment owner | `BLOCKED_EXTERNAL` | فراهم‌کردن همه‌ی staging dependencies |
| Release | Release owner | `APPROVAL_REQUIRED` | ثبت go/no-go انسانی |

## Release Rule

Release فقط زمانی می‌تواند `production_ready` شود که همه‌ی gateهای production-critical برابر PASS یا PASS_STAGING باشند و Human Approval برابر `APPROVED` ثبت شود. تا آن زمان وضعیت رسمی:

`blocked_for_production`
