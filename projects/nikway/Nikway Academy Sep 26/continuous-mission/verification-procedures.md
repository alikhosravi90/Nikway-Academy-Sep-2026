# NIKWAY External Verification Procedures

این سند procedureهای deterministic برای اجرای بعدی است. هیچ secret در این فایل یا evidence ذخیره نمی‌شود.

## PostgreSQL staging

1. `DATABASE_URL` را فقط از secret manager یا CI secret inject کن.
2. با role اجرایی وصل شو و مالک، superuser و grants را ثبت کن.
3. `db/v1_schema.sql` را در staging اعمال کن.
4. تست‌های persistence، transaction rollback، RLS و organization isolation را اجرا کن:

```powershell
python -m pytest tests/test_postgres_repository_integration.py tests/test_persistence.py tests/test_audit_event_persistence.py tests/test_progression_trace.py -q
```

5. نتیجه را فقط `PASS_STAGING` یا `BLOCKED_EXTERNAL` ثبت کن.

### Local non-owner runtime-role verification

برای حذف blockerهای داخلی بدون ادعای staging، اجرای ایزولهٔ compose را با
`docker compose -f docker-compose.full-v1.yml` و متغیرهای
`NIKWAY_POSTGRES_PASSWORD` و `NIKWAY_RUNTIME_PASSWORD` موقت انجام بده.
این فایل نام پیش‌فرض Compose نیست و باید با `-f` صریح انتخاب شود.
compose باید bootstrap role را از runtime role جدا کند و `OIDC_JWKS_URL` را نیز
به‌صورت required بررسی کند. پس از بالا آمدن PostgreSQL، این موارد را ثبت کن:

```sql
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole
FROM pg_roles
WHERE rolname IN ('nikway_bootstrap', 'nikway_runtime');
SELECT c.relname, pg_get_userbyid(c.relowner) AS owner
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r';
```

نتیجهٔ این مسیر فقط `PASS_LOCAL` است؛ جایگزین `PASS_STAGING` نیست.

## OIDC/JWKS

Required environment names: `OIDC_ISSUER_URL`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`.

```powershell
python -m pytest tests/test_auth.py tests/test_protected_endpoints.py -q
```

با provider واقعی، token معتبر، نامعتبر، منقضی، بدون token، سازمان اشتباه و role اشتباه را اجرا کن. بدون provider واقعی نتیجه `BLOCKED_EXTERNAL` است.

OIDC/JWKS local preflight:

1. Fetch discovery and verify HTTP 200.
2. Verify the discovered issuer exactly matches `OIDC_ISSUER_URL`.
3. Fetch `OIDC_JWKS_URL` and verify HTTP 200 plus a non-empty key set.
4. Run `python -m pytest tests/test_oidc_jwks.py tests/test_auth.py tests/test_protected_endpoints.py -q`.
5. Classify discovery/JWKS reachability as `PASS_LOCAL_PROVIDER_SMOKE` only; it is not staging evidence.
6. Execute provider-issued token cases only after the approved issuer, audience, JWKS endpoint, and test credentials are supplied.

## S3-compatible storage

Required names: `S3_ENDPOINT_URL`, `S3_BUCKET`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.

```powershell
python -m pytest tests/test_s3_client.py tests/test_storage.py tests/test_evidence_persistence.py -q
```

در staging علاوه بر upload، checksum، object key سازمانی، metadata، read، failure، cleanup، rollback و duplicate request را ثبت کن. MinIO local برابر staging verified نیست.

## Real staging E2E

ترتیب اجرا:

`OIDC authentication → user/organization resolution → authorization → transaction → persistence → upload → event → audit → idempotency → RLS isolation → failure → rollback → cleanup`

E2E فقط با تمام وابستگی‌های staging می‌تواند `PASS_STAGING` شود.

پیش‌شرط محلی suite نیز قابل بررسی است:

```powershell
python -m pytest tests/test_e2e_preflight.py -q
```

این تست وجود contract و procedure و کامل بودن فهرست caseها را بررسی می‌کند؛
در نبود credential یا endpoint واقعی، اجرای staging را skip و `BLOCKED_EXTERNAL`
ثبت می‌کند.

## Local CI-equivalent security scan

برای اجرای معادل محلی مرحلهٔ Trivy بدون ادعای اجرای GitHub Actions:

```powershell
docker run --rm `
  -v "${PWD}:/workspace" `
  -v nikway-trivy-cache:/root/.cache/trivy `
  aquasec/trivy:0.66.0 fs `
  --scanners vuln,secret `
  --severity CRITICAL,HIGH `
  --ignore-unfixed `
  --exit-code 1 `
  --format json `
  --output /workspace/trivy-local-equivalent-YYYY-MM-DD.json `
  /workspace
```

نتیجهٔ این فرمان `PASS_LOCAL` است؛ اجرای رسمی workflow همچنان باید در CI ثبت شود.

## Operational smoke

برای ثبت وضعیت سرویس‌های محلی بدون تغییر state:

```powershell
python scripts/operational_smoke.py
```

این فرمان health API، discovery و JWKS محلی OIDC، health MinIO و inventory
سرویس‌های Docker را ثبت می‌کند. پاسخ `404` برای endpointی که در image فعلی
وجود ندارد `NOT_APPLICABLE` است و هرگز به‌عنوان موفقیت ثبت نمی‌شود.
