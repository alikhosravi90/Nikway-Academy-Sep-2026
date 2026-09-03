# Nikway Academy Sep 26

این بسته برای تبدیل اسناد معماری NIKWAY به یک مدل سلسله‌مراتبی و سپس سنتز آن‌ها ساخته شده است.

ساختار هر artifact محتوایی:

- Level 0: خود artifact و هویت آن
- Level 1: بخش‌های اصلی و مسئولیت‌های artifact
- Level 2: جزئیات اجرایی هر بخش

فرایند سنتز:

`Extract → Normalize → Relate → Resolve → Synthesize`

فایل `NIKWAY-MASTER.yaml` سند واحد مقصد است؛ `manifest.yaml` نقطه ورود بسته و `black-manifest.yaml` قانون اساسی معماری است.
