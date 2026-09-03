# NIKWAY V1 Publish-Ready Sample

Status: `ready_for_review`

این نمونه خروجی نهایی هفت مرحله است و برای انتشار بیرونی هنوز به تأیید انسانی و اجرای واقعی PostgreSQL/OIDC/restore test نیاز دارد.

## Demonstrated journey

```text
Organization → User/Membership → Learning Journey → Assignment
→ Evidence → Assessment Result → Progression Event → Progress Report
```

## V1 boundary

- One modular monolith
- One PostgreSQL database
- OIDC authentication
- S3-compatible evidence storage
- Postgres-backed events/jobs
- No Redis, Neo4j, pgvector, RAG, LLM, microservices, or Kubernetes
