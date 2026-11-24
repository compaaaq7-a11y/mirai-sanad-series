# أدوات الذكاء الاصطناعي المجانية لصناعة الفيديو

كل الأدوات هنا مجانية ومفتوحة المصدر، وتعمل على المعالج العادي (CPU) بدون كرت شاشة.
التثبيت بأمر واحد:

```bash
bash tools/install-free-ai-tools.sh
```

## ما تم تثبيته ولماذا

| الأداة | وظيفتها في المشروع | الحالة |
| --- | --- | --- |
| [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | المحرك الأساسي: نص ← فيديو كامل | يعمل |
| [Piper](https://github.com/OHF-Voice/piper1-gpl) | صوت عربي محلي بدون إنترنت (`ar_JO-kareem-medium`) | جُرّب ويعمل |
| [edge-tts](https://github.com/rany2/edge-tts) | أصوات Microsoft العربية (سعودي/مصري...) | يعمل على GitHub Actions وعلى جهازك |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | تفريغ الصوت وترجمة SRT بتوقيت الكلمة | جُرّب ويعمل (نموذج `small`) |
| stable-ts | توقيت أدق للترجمة | مثبت |
| MoviePy 2 + Pillow | تركيب الفيديو والنصوص العربية | جُرّب ويعمل |
| [mcp-video / Kinocut](https://github.com/pastorsimon1798/mcp-video) | خادم MCP يتيح لـ Claude قص ودمج وترجمة الفيديو عبر ffmpeg | مضاف في `.mcp.json` |
| yt-dlp, pydub | تنزيل مقاطع مرجعية، قص الصوت | مثبت |

## أمثلة سريعة

صوت عربي محلي:

```bash
echo "مرحباً بكم في ميراي سند" | .venv/bin/piper -m vendor/piper/ar_JO-kareem-medium.onnx -f voice.wav
```

صوت Edge:

```bash
.venv/bin/edge-tts --voice ar-SA-HamedNeural --text "مرحباً" --write-media voice.mp3
```

ترجمة نصية تلقائية:

```python
from faster_whisper import WhisperModel
m = WhisperModel("small", device="cpu", compute_type="int8")
segments, _ = m.transcribe("voice.wav", language="ar", word_timestamps=True)
```

نص عربي على صورة (مهم: استخدم محرك raqm ولا تستخدم arabic-reshaper معه، وإلا تتقطع الحروف):

```python
from PIL import Image, ImageDraw, ImageFont
f = ImageFont.truetype("Cairo-Regular.ttf", 72, layout_engine=ImageFont.Layout.RAQM)
ImageDraw.Draw(img).text((x, y), "ميراي سند", font=f, direction="rtl")
```

## ملاحظات

- عند تنزيل نماذج Whisper من Hugging Face وفشل التنزيل، جرّب `HF_HUB_DISABLE_XET=1`.
- `av` مثبّت على إصدار أقل من 16 لأن الإصدار 19 يكسر faster-whisper حالياً.
- edge-tts يحتاج اتصال WebSocket بخوادم Microsoft، لذلك لا يعمل خلف بعض البروكسيات؛ استخدم Piper بديلاً محلياً.

## نماذج توليد فيديو بالذكاء الاصطناعي (تحتاج كرت شاشة)

لم تُثبّت هنا لأنها تحتاج GPU قوي، لكنها مجانية ومفتوحة المصدر للمستقبل:

- **LTX-Video**: الأسرع، مناسب لـ ComfyUI.
- **Wan 2.1 / 2.2**: أعلى جودة مفتوحة المصدر (نموذج 5B يحتاج كرت بمستوى RTX 4090).
- **HunyuanVideo**، **CogVideoX** (له دفاتر Colab مجانية)، **Open-Sora**.
- **ComfyUI**: الواجهة المعتادة لتشغيل هذه النماذج.

أصوات عربية مفتوحة المصدر للتجربة لاحقاً: SILMA TTS (يدعم التشكيل، MIT/Apache)، Habibi-TTS (لهجات، غير تجاري).
