# ميراي سند 🎬

سلسلة فيديوهات عربية قصيرة. كل حلقة تتحول تلقائياً إلى فيديو كامل (صوت عربي، ترجمة نصية، لقطات، موسيقى)
باستخدام أداة [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo).

## كيف تعمل

1. تكتب نصوص الحلقات في ملف `series.toml`.
2. يحوّل `mirai.py` كل حلقة إلى فيديو عبر MoneyPrinterTurbo.
3. تجد الفيديوهات في مجلد `output/` باسم كل حلقة.

## الطريقة الأسهل: على GitHub بدون أي تثبيت

عند كل تعديل على `series.toml` ورفعه، يعمل GitHub Actions تلقائياً ويولّد كل الحلقات.

- لتحميل الفيديوهات: تبويب **Actions** ← آخر تشغيل ← **Artifacts** ← `mirai-sanad-videos`،
  أو من فرع `videos` الذي يحوي دائماً آخر نسخة من الحلقات.
- لتوليد حلقة معيّنة يدوياً: **Actions** ← **توليد حلقات ميراي سند** ← **Run workflow**، واكتب اسم الحلقة (مثل `ep02-ai-tools`).
- للقطات فيديو حقيقية: سجّل مجاناً في [Pixabay](https://pixabay.com/accounts/register/) ثم انسخ مفتاحك من
  [صفحة الـ API](https://pixabay.com/api/docs/)، وأضفه في
  **Settings ← Secrets and variables ← Actions** باسم `PIXABAY_API_KEY`.
  (يُقبل أيضاً `PEXELS_API_KEY` أو `COVERR_API_KEY`؛ إصدار مفاتيح Pexels الجديدة متوقف حالياً.)
  بدون مفتاح تُستخدم الصور والمقاطع الموجودة في `assets/`، أو خلفية بلون واحد.

## على جهازك

المتطلبات: Python 3.11 أو أحدث، و`ffmpeg`، و`git`.

```bash
python3 mirai.py setup        # مرة واحدة: تنزيل الأداة وتثبيتها
python3 mirai.py list         # عرض الحلقات
python3 mirai.py generate     # توليد كل الحلقات
python3 mirai.py generate ep01-intro ep03-learning   # حلقات محددة
```

مع مفتاح Pixabay:

```bash
PIXABAY_API_KEY=مفتاحك python3 mirai.py generate
```

خيارات أخرى:

- `--source local` لاستخدام لقطاتك من مجلد `assets/`.
- `--voice ar-EG-SalmaNeural-Female` لتغيير الصوت لكل الحلقات.

## إضافة حلقة جديدة

أضف في آخر `series.toml`:

```toml
[[episodes]]
id = "ep06-new"
title = "عنوان الحلقة"
terms = "english, search, words"
script = """
نص الحلقة هنا.
"""
```

- `terms` كلمات إنجليزية للبحث عن اللقطات في Pixabay أو Pexels.
- أي إعداد من `[defaults]` يمكن تغييره لحلقة واحدة بكتابته داخلها، مثل `voice_name` أو `video_aspect`.

## الأصوات العربية المجانية

| الصوت | اللهجة |
| --- | --- |
| `ar-SA-HamedNeural-Male` | سعودي، رجل |
| `ar-SA-ZariyahNeural-Female` | سعودي، امرأة |
| `ar-EG-ShakirNeural-Male` | مصري، رجل |
| `ar-EG-SalmaNeural-Female` | مصري، امرأة |
