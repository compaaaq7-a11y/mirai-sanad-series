#!/usr/bin/env python3
"""توليد صور مجاني بدون حساب ولا مفتاح عبر Pollinations (image.pollinations.ai).

  imagegen.py "وصف الصورة بالإنجليزية أفضل" -o out.jpg [--w 1080 --h 1920] [--seed 7] [--model flux]

- يعيد المحاولة تلقائياً عند الانشغال (503/429).
- يقص شعار pollinations.ai من أسفل الصورة (يطلب صورة أطول بقليل ثم يقصها).
- الخدمة المجانية تعطي 576x1024 كحد أقصى، فتُكبَّر بـ Real-ESRGAN إلى 1152x2048 (scripts/upscale.py).
- يحفظ نسخة مخبأة: نفس الوصف + المقاس + البذرة = نفس الملف بدون طلب جديد.
- اختياري: متغير البيئة POLLINATIONS_TOKEN لحساب مجاني يرفع الحدود ويتيح نماذج أقوى.
"""
import argparse, hashlib, os, subprocess, sys, time, urllib.parse, urllib.request

HOST = 'https://image.pollinations.ai/prompt/'
LOGO_CROP = 0.06  # نسبة الارتفاع الإضافية التي تُطلب ثم تُقص (مكان الشعار)


def cache_name(prompt, w, h, seed, model):
    key = f'{prompt}|{w}x{h}|{seed}|{model}'.encode()
    return hashlib.sha1(key).hexdigest()[:16] + '.jpg'


def generate(prompt, out, w=1080, h=1920, seed=7, model=None, tries=8, quiet=False):
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return out
    # الخدمة المجانية تعطي بحد أقصى ~1024 للضلع الأطول؛ نطلب بنفس النسبة ثم نكبّر
    scale = min(1.0, 1024 / (h * (1 + LOGO_CROP)))
    rw, rh = int(w * scale) // 8 * 8, int(h * (1 + LOGO_CROP) * scale) // 8 * 8
    q = {'width': rw, 'height': rh, 'seed': seed, 'nologo': 'true', 'enhance': 'false'}
    if model:
        q['model'] = model
    url = HOST + urllib.parse.quote(prompt) + '?' + urllib.parse.urlencode(q)
    headers = {'User-Agent': 'salam-skill/1.0'}
    tok = os.environ.get('POLLINATIONS_TOKEN')
    if tok:
        headers['Authorization'] = 'Bearer ' + tok
    raw = out + '.part'
    delay = 6
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=180) as r:
                data = r.read()
                if not r.headers.get('content-type', '').startswith('image/'):
                    raise RuntimeError('not an image: ' + data[:200].decode('utf8', 'replace'))
            open(raw, 'wb').write(data)
            break
        except Exception as e:  # 503/429/مهلة: انتظر وأعد
            if i == tries - 1:
                raise RuntimeError(f'image generation failed after {tries} tries: {e}')
            if not quiet:
                print(f'  busy ({getattr(e, "code", e)}), retry in {delay}s...', file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 1.5, 30)
    # قص الشعار من الأسفل، ثم تكبير بالذكاء الاصطناعي (Real-ESRGAN) لصورة أوضح وأدق
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import upscale
    oh = 2048 if h >= w else int(round(2048 * h / w / 2)) * 2
    ow = int(round(oh * w / h / 2)) * 2
    method = upscale.upscale(raw, out, ow, oh, crop_bottom=LOGO_CROP / (1 + LOGO_CROP))
    if not quiet:
        print(f'  image {ow}x{oh} ({method})', file=sys.stderr)
    os.remove(raw)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('prompt')
    ap.add_argument('-o', required=True)
    ap.add_argument('--w', type=int, default=1080)
    ap.add_argument('--h', type=int, default=1920)
    ap.add_argument('--seed', type=int, default=7)
    ap.add_argument('--model')
    a = ap.parse_args()
    print(generate(a.prompt, a.o, a.w, a.h, a.seed, a.model))


if __name__ == '__main__':
    main()
