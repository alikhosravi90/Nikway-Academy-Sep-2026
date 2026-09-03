# Level 2 — Operational Store

این سطح برای اجرای عملیاتی استفاده می‌شود و از Source of Truth مشتق و با آن همگام می‌گردد.

- PostgreSQL: رکوردهای تراکنشی و رجیستری‌ها
- pgvector: embedding و semantic search
- Neo4j: graph روابط و provenance
- Object Storage: فایل، تصویر، log، report و evidence

Secret واقعی نباید در این package یا PostgreSQL عادی ذخیره شود؛ فقط reference و metadata نگهداری می‌شود.
