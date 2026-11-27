#!/usr/bin/env python3
"""تكبير الصور بالذكاء الاصطناعي (Real-ESRGAN x2) على المعالج، لصور أوضح وأدق.

  upscale.py in.jpg -o out.jpg [--w 1152 --h 2048]

- يحتاج: pip install torch spandrel "opencv-contrib-python-headless<5"
  والنموذج يُنزَّل تلقائياً مرة واحدة إلى ~/.cache/salam-skill/sr/ (67MB من GitHub).
- إن لم تتوفر المتطلبات: تكبير Lanczos مع حدّة خفيفة (أقل دقة لكنه يعمل دائماً).
- الناتج يُقص من المنتصف إلى النسبة المطلوبة (9:16 افتراضياً) دون تمطيط.
"""
import argparse, os, subprocess, sys, urllib.request

MODEL_URL = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth'
MODEL = os.path.expanduser('~/.cache/salam-skill/sr/RealESRGAN_x2plus.pth')
_model = None


def _load():
    global _model
    if _model is None:
        import torch  # noqa: F401
        from spandrel import ModelLoader
        if not os.path.exists(MODEL):
            os.makedirs(os.path.dirname(MODEL), exist_ok=True)
            print('  downloading Real-ESRGAN model (67MB, once)...', file=sys.stderr)
            urllib.request.urlretrieve(MODEL_URL, MODEL + '.part')
            os.replace(MODEL + '.part', MODEL)
        _model = ModelLoader().load_from_file(MODEL).model.eval()
    return _model


def esrgan_x2(img):
    """img: مصفوفة RGB float32 [0..1] بأبعاد HxWx3 → ضعف الأبعاد. يعمل بمربعات لتوفير الذاكرة."""
    import torch
    m = _load()
    x = torch.from_numpy(img).permute(2, 0, 1)[None]
    _, _, H, W = x.shape
    T, P = 256, 12
    out = torch.zeros(1, 3, H * 2, W * 2)
    with torch.inference_mode():
        for y in range(0, H, T):
            for x0 in range(0, W, T):
                y1, x1 = max(0, y - P), max(0, x0 - P)
                y2, x2 = min(H, y + T + P), min(W, x0 + T + P)
                o = m(x[:, :, y1:y2, x1:x2])
                oy, ox = (y - y1) * 2, (x0 - x1) * 2
                h, w = min(T, H - y) * 2, min(T, W - x0) * 2
                out[:, :, y * 2:y * 2 + h, x0 * 2:x0 * 2 + w] = o[:, :, oy:oy + h, ox:ox + w]
    return out[0].permute(1, 2, 0).clamp(0, 1).numpy()


def center_crop(img, aspect):
    h, w = img.shape[:2]
    if w / h > aspect:
        nw = int(round(h * aspect))
        return img[:, (w - nw) // 2:(w - nw) // 2 + nw]
    nh = int(round(w / aspect))
    return img[(h - nh) // 2:(h - nh) // 2 + nh]


def upscale(src, dst, W=1152, H=2048, crop_bottom=0.0):
    """crop_bottom: نسبة تُقص من الأسفل أولاً (مكان شعار الخدمة المجانية)."""
    try:
        import cv2, numpy as np
        img = cv2.cvtColor(cv2.imread(src), cv2.COLOR_BGR2RGB)
        if crop_bottom:
            img = img[:int(img.shape[0] * (1 - crop_bottom))]
        img = center_crop(img, W / H)
        try:
            up = esrgan_x2(img.astype(np.float32) / 255)
            up = (up * 255).round().astype(np.uint8)
            method = 'Real-ESRGAN x2'
        except Exception as e:  # بدون torch/spandrel أو تعذّر تنزيل النموذج
            print(f'  Real-ESRGAN unavailable ({e.__class__.__name__}); using Lanczos', file=sys.stderr)
            up, method = img, 'Lanczos'
        interp = cv2.INTER_AREA if up.shape[1] >= W else cv2.INTER_LANCZOS4
        up = cv2.resize(up, (W, H), interpolation=interp)
        if method == 'Lanczos':
            blur = cv2.GaussianBlur(up, (0, 0), 1.2)
            up = cv2.addWeighted(up, 1.5, blur, -0.5, 0)
        cv2.imwrite(dst, cv2.cvtColor(up, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])
        return method
    except ImportError:
        # بدون OpenCV: ffmpeg (قص + Lanczos + حدّة)
        vf = (f'crop=iw:ih*{1 - crop_bottom:.4f}:0:0,' if crop_bottom else '') + \
             f'scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},unsharp=5:5:0.6'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', vf, '-q:v', '2', dst], check=True)
        return 'ffmpeg Lanczos'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src')
    ap.add_argument('-o', required=True)
    ap.add_argument('--w', type=int, default=1152)
    ap.add_argument('--h', type=int, default=2048)
    a = ap.parse_args()
    print(upscale(a.src, a.o, a.w, a.h))


if __name__ == '__main__':
    main()
