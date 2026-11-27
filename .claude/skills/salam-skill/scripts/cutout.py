#!/usr/bin/env python3
"""قص خلفية صورة تلقائياً (مجاناً، على المعالج) لصنع ملصقات الكولاج.

  cutout.py in.jpg -o out.png [--model isnet-general-use]

- يستخدم rembg (pip install "rembg[cpu]"). النموذج يُنزَّل مرة واحدة من GitHub إلى ~/.u2net/.
- الناتج PNG شفاف، مقصوص على حدود العنصر مع هامش صغير، فيُستخدم مباشرة في `stickers=`.
"""
import argparse, sys


def cutout(src, dst, model='isnet-general-use'):
    from rembg import remove, new_session
    from PIL import Image
    img = Image.open(src).convert('RGB')
    out = remove(img, session=new_session(model), post_process_mask=True)
    # تنظيف: إزالة البقايا الصغيرة المنفصلة والحواف شبه الشفافة (تظهر بقعاً بيضاء مع حدّ الملصق)
    try:
        import numpy as np
        from scipy import ndimage
        a = np.array(out.getchannel('A'))
        a[a < 60] = 0
        lab, n = ndimage.label(a > 0)
        if n > 1:
            sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
            big = [i + 1 for i, sz in enumerate(sizes) if sz >= 0.02 * sizes.max()]
            a[~np.isin(lab, big)] = 0
        out.putalpha(Image.fromarray(a))
    except ImportError:
        pass
    bbox = out.getchannel('A').point(lambda a: 255 if a > 20 else 0).getbbox()
    if bbox:
        pad = int(max(out.size) * 0.02)
        x0, y0, x1, y1 = bbox
        out = out.crop((max(0, x0 - pad), max(0, y0 - pad), min(out.width, x1 + pad), min(out.height, y1 + pad)))
    out.save(dst)
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src')
    ap.add_argument('-o', required=True)
    ap.add_argument('--model', default='isnet-general-use')
    a = ap.parse_args()
    print(cutout(a.src, a.o, a.model))


if __name__ == '__main__':
    sys.exit(main())
