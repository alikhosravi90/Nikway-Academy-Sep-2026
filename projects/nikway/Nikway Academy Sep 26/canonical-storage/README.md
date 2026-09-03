# NIKWAY Canonical Storage Package

این بسته سه سطح ذخیره‌سازی مرجع NIKWAY را یکپارچه می‌کند:

```text
Source of Truth → Operational Store → Derived Views
```

## Level 1 — Source of Truth

فایل‌های version-controlled شامل YAML، Markdown، JSON، JSON Schema و OpenAPI هستند. این سطح مرجع انسانی و قابل بازبینی است.

## Level 2 — Operational Store

مدل اجرایی برای PostgreSQL، pgvector، Neo4j و Object Storage است. این سطح برای اجرای پنل، Fact، Decision، Task، User، Release، Audit، جست‌وجوی معنایی، روابط و فایل‌ها استفاده می‌شود.

## Level 3 — Derived Views

خروجی‌های تولیدشده از دو سطح قبلی شامل Master، Graph Export، Search Index، Dashboard، گزارش و داده صفحه عمومی Launch هستند.

## قانون حاکم

Derived View قابل ویرایش مرجع نیست. تغییرات باید در Source of Truth ثبت شوند، سپس به Operational Store وارد و Viewها دوباره تولید شوند.
