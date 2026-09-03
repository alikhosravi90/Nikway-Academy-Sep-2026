# NIKWAY Continuous Publish Mission

این پوشه یک مأموریت پیوسته اما محدود برای ساخت نمونه قابل انتشار NIKWAY V1 تعریف می‌کند.

چرخه همیشه فقط هفت مرحله دارد و هر اجرای آن یک `mission_run_id`، حداکثر تعداد iteration و یک نقطه توقف دارد:

```text
Discover → Design → Build → Verify → Harden → Package → Release Review
```

مأموریت در صورت رسیدن به `blocked` وارد loop بی‌نهایت نمی‌شود:

1. مشکل در `challenge-registry.yaml` ثبت می‌شود؛
2. حداکثر دو تلاش اصلاحی انجام می‌شود؛
3. اگر حل نشد، مسیر fallback همان مرحله اجرا می‌شود؛
4. در صورت نبود fallback، وضعیت `blocked_for_human` صادر و run متوقف می‌شود.

انتشار بیرونی، ارسال، deploy یا تغییر production بدون تأیید انسانی انجام نمی‌شود.
