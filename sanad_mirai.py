#!/usr/bin/env python3
"""حلقات ميراي وسند الحوارية: رسوم + صوتان + ترجمة عربية، بأدوات مجانية فقط.

الاستخدام:
    python3 sanad_mirai.py                    # كل الحلقات في dialogues/
    python3 sanad_mirai.py ep06-lets-plant    # حلقة محددة
    python3 sanad_mirai.py --tts piper        # إجبار الصوت المحلي

الصوت: edge-tts (أصوات Microsoft المجانية) وإن تعذّر فـ Piper المحلي.
الرسوم: Pillow مع محرك raqm لتشكيل الحروف العربية، والخطوط في assets/fonts/.
التركيب: ffmpeg.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

ROOT = Path(__file__).resolve().parent
DIALOGUES = ROOT / "dialogues"
FONTS = ROOT / "assets" / "fonts"
OUTPUT = ROOT / "output"
BUILD = ROOT / "build" / "dialogue"
PIPER_MODEL = ROOT / "vendor" / "piper" / "ar_JO-kareem-medium.onnx"
SONGS = ROOT / "vendor" / "MoneyPrinterTurbo" / "resource" / "songs"

W, H = 1080, 1920
SS = 2            # رسم بدقة مضاعفة ثم تصغير لحواف ناعمة
FPS = 30
GAP = 0.35        # صمت بعد كل جملة (ثانية)

CHARACTERS = {
    "mirai": {"name": "ميراي", "color": (142, 84, 233), "edge": "ar-SA-ZariyahNeural",
              "piper_pitch": 1.22, "side": "right"},
    "sanad": {"name": "سند", "color": (30, 150, 110), "edge": "ar-SA-HamedNeural",
              "piper_pitch": 1.0, "side": "left"},
}

INK = (40, 36, 52)
WHITE = (255, 255, 255)
SOIL = (110, 72, 48)
POT = (205, 105, 70)
LEAF = (72, 170, 80)
LEAF_DARK = (46, 120, 60)


def log(msg: str) -> None:
    print(f"[ميراي وسند] {msg}", file=sys.stderr, flush=True)


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def ffprobe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


# ------------------------------------------------------------------ رسم
def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size * SS, layout_engine=ImageFont.Layout.RAQM)


class Canvas:
    """رسم بإحداثيات 1080×1920 على لوح أكبر بـ SS مرة."""

    def __init__(self, bg=(255, 255, 255)):
        self.img = Image.new("RGB", (W * SS, H * SS), bg)
        self.d = ImageDraw.Draw(self.img, "RGBA")

    @staticmethod
    def s(*v):
        return [round(x * SS) for x in v]

    def ellipse(self, box, **kw):
        if "width" in kw:
            kw["width"] = round(kw["width"] * SS)
        self.d.ellipse(self.s(*box), **kw)

    def rect(self, box, r=0, **kw):
        if "width" in kw:
            kw["width"] = round(kw["width"] * SS)
        self.d.rounded_rectangle(self.s(*box), radius=r * SS, **kw)

    def poly(self, pts, **kw):
        self.d.polygon([tuple(self.s(*p)) for p in pts], **kw)

    def line(self, pts, width, **kw):
        self.d.line([tuple(self.s(*p)) for p in pts], width=round(width * SS), **kw)

    def arc(self, box, start, end, width, **kw):
        self.d.arc(self.s(*box), start, end, width=round(width * SS), **kw)

    def text_w(self, text, f) -> float:
        return self.d.textlength(text, font=f, direction="rtl") / SS

    def text(self, xy, text, f, fill, anchor="mm", stroke=0, stroke_fill=None):
        self.d.text(tuple(self.s(*xy)), text, font=f, fill=fill, anchor=anchor, direction="rtl",
                    stroke_width=round(stroke * SS), stroke_fill=stroke_fill)

    def final(self) -> Image.Image:
        return self.img.resize((W, H), Image.LANCZOS)


def vertical_gradient(c: Canvas, box, top, bottom):
    x0, y0, x1, y1 = box
    steps = int(y1 - y0)
    for i in range(steps):
        t = i / max(steps - 1, 1)
        col = tuple(round(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        c.rect((x0, y0 + i, x1, y0 + i + 1.5), fill=col)


def wrap(c: Canvas, text: str, f, max_w: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if c.text_w(trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# --------------------------------------------------------------- عناصر المشهد
SCENE_TOP, SCENE_BOTTOM = 250, 1230
GROUND_Y = 1090


def draw_sky(c: Canvas):
    c.rect((40, SCENE_TOP, W - 40, SCENE_BOTTOM), r=48, fill=(190, 228, 250))
    vertical_gradient(c, (40, SCENE_TOP + 40, W - 40, GROUND_Y), (170, 220, 250), (232, 246, 236))
    # الشمس
    cx, cy = 880, 400
    for a in range(0, 360, 30):
        r1, r2 = 85, 120
        c.line([(cx + r1 * math.cos(math.radians(a)), cy + r1 * math.sin(math.radians(a))),
                (cx + r2 * math.cos(math.radians(a)), cy + r2 * math.sin(math.radians(a)))],
               width=10, fill=(255, 196, 60))
    c.ellipse((cx - 70, cy - 70, cx + 70, cy + 70), fill=(255, 205, 70))
    # غيوم
    for gx, gy, k in ((230, 380, 1.0), (520, 470, 0.7)):
        for dx, dy, r in ((0, 0, 50), (55, -20, 60), (115, 0, 48), (55, 15, 50)):
            c.ellipse((gx + dx * k - r * k, gy + dy * k - r * k, gx + dx * k + r * k, gy + dy * k + r * k),
                      fill=(255, 255, 255, 235))
    # الأرض
    c.rect((40, GROUND_Y, W - 40, SCENE_BOTTOM), r=48, fill=(126, 190, 96))
    c.rect((40, GROUND_Y, W - 40, GROUND_Y + 60), fill=(126, 190, 96))
    random.seed(7)
    for _ in range(40):
        x = random.uniform(70, W - 70)
        y = random.uniform(GROUND_Y + 20, SCENE_BOTTOM - 30)
        c.line([(x, y), (x - 6, y - 18)], width=4, fill=(96, 160, 72))


def draw_pot(c: Canvas, cx=540, base=GROUND_Y + 60, soil_hole=False):
    top = base - 230
    c.poly([(cx - 190, top + 40), (cx + 190, top + 40), (cx + 145, base), (cx - 145, base)], fill=POT)
    c.rect((cx - 215, top, cx + 215, top + 60), r=18, fill=(225, 125, 85))
    c.ellipse((cx - 185, top - 22, cx + 185, top + 30), fill=SOIL)
    if soil_hole:
        c.ellipse((cx - 45, top - 8, cx + 45, top + 16), fill=(70, 44, 30))
    return top  # مستوى التربة


def draw_seed(c: Canvas, cx, cy, scale=1.0, angle_tilt=0):
    rw, rh = 34 * scale, 22 * scale
    c.ellipse((cx - rw, cy - rh, cx + rw, cy + rh), fill=(214, 170, 96), outline=(150, 110, 60), width=3 * scale)
    c.arc((cx - rw * 0.6, cy - rh * 0.5, cx + rw * 0.6, cy + rh * 0.5), 200, 340, width=3 * scale, fill=(170, 125, 70))


def draw_leaf(c: Canvas, x, y, length, angle, color=LEAF):
    a = math.radians(angle)
    tip = (x + length * math.cos(a), y - length * math.sin(a))
    n = (-math.sin(a), -math.cos(a))
    mid = ((x + tip[0]) / 2, (y + tip[1]) / 2)
    wdt = length * 0.32
    c.poly([(x, y), (mid[0] + n[0] * wdt, mid[1] + n[1] * wdt), tip, (mid[0] - n[0] * wdt, mid[1] - n[1] * wdt)],
           fill=color)
    c.line([(x, y), tip], width=3, fill=LEAF_DARK)


def draw_plant(c: Canvas, soil_y, height, leaves, flowers=0, fruits=0):
    cx = 540
    stem_top = soil_y - height
    c.line([(cx, soil_y), (cx + 8, soil_y - height * 0.5), (cx, stem_top)], width=14, fill=LEAF_DARK)
    for i in range(leaves):
        y = soil_y - height * (0.25 + 0.7 * i / max(leaves - 1, 1)) if leaves > 1 else stem_top
        side = 1 if i % 2 == 0 else -1
        length = 120 - 40 * (i / max(leaves, 1)) if leaves > 2 else 95
        draw_leaf(c, cx, y, length, 25 if side > 0 else 155)
    spots = [(-150, 0.55), (140, 0.45), (-110, 0.85), (120, 0.75), (0, 1.02), (-60, 0.3)]
    for i in range(flowers):
        dx, f = spots[i % len(spots)]
        fx, fy = cx + dx * 0.8, soil_y - height * f
        for k in range(5):
            a = math.radians(k * 72)
            c.ellipse((fx + 18 * math.cos(a) - 13, fy + 18 * math.sin(a) - 13,
                       fx + 18 * math.cos(a) + 13, fy + 18 * math.sin(a) + 13), fill=(255, 214, 64))
        c.ellipse((fx - 10, fy - 10, fx + 10, fy + 10), fill=(240, 150, 40))
    for i in range(fruits):
        dx, f = spots[(i + 2) % len(spots)]
        tx, ty = cx + dx, soil_y - height * f + 40
        c.ellipse((tx - 42, ty - 38, tx + 42, ty + 40), fill=(226, 58, 52))
        c.ellipse((tx - 22, ty - 24, tx - 6, ty - 10), fill=(255, 150, 140))
        c.poly([(tx, ty - 50), (tx - 18, ty - 32), (tx + 18, ty - 32)], fill=LEAF_DARK)


def sparkle(c: Canvas, x, y, r, color=(255, 220, 90)):
    c.poly([(x, y - r), (x + r * 0.25, y - r * 0.25), (x + r, y), (x + r * 0.25, y + r * 0.25),
            (x, y + r), (x - r * 0.25, y + r * 0.25), (x - r, y), (x - r * 0.25, y - r * 0.25)], fill=color)


def scene_seed(c: Canvas):
    draw_sky(c)
    c.ellipse((360, 600, 720, 960), fill=(255, 255, 255, 150))
    draw_seed(c, 540, 780, scale=3.2)
    for x, y, r in ((420, 640, 30), (680, 690, 22), (650, 900, 26)):
        sparkle(c, x, y, r)


def scene_needs(c: Canvas):
    draw_sky(c)
    label = font("Tajawal-ExtraBold.ttf", 46)
    # تربة
    c.poly([(150, 760), (330, 760), (305, 900), (175, 900)], fill=POT)
    c.ellipse((150, 735, 330, 785), fill=SOIL)
    # ماء
    c.poly([(540, 680), (480, 800), (600, 800)], fill=(70, 160, 235))
    c.ellipse((478, 750, 602, 880), fill=(70, 160, 235))
    c.ellipse((510, 780, 535, 815), fill=(200, 235, 255))
    # شمس صغيرة
    c.ellipse((790, 720, 930, 860), fill=(255, 205, 70))
    for x, t in ((240, "تربة"), (540, "ماء"), (860, "شمس")):
        c.rect((x - 95, 950, x + 95, 1030), r=40, fill=(255, 255, 255, 230))
        c.text((x, 990), t, label, INK)


def scene_plant_seed(c: Canvas):
    draw_sky(c)
    soil = draw_pot(c, soil_hole=True)
    draw_seed(c, 540, soil - 170, scale=1.3)
    c.line([(540, soil - 120), (540, soil - 40)], width=8, fill=(255, 255, 255))
    c.poly([(520, soil - 50), (560, soil - 50), (540, soil - 20)], fill=(255, 255, 255))


def scene_water(c: Canvas):
    draw_sky(c)
    soil = draw_pot(c)
    # مرشّة ماء
    c.poly([(640, 520), (820, 520), (800, 660), (660, 660)], fill=(80, 140, 220))
    c.line([(650, 560), (520, 640)], width=22, fill=(80, 140, 220))
    c.ellipse((495, 620, 545, 670), fill=(60, 120, 200))
    c.arc((780, 500, 880, 620), 270, 90, width=16, fill=(60, 120, 200))
    for i, (x, y) in enumerate(((500, 720), (530, 760), (470, 780), (515, 820), (545, 700))):
        c.ellipse((x - 9, y - 14, x + 9, y + 14), fill=(110, 190, 250))


def scene_wait(c: Canvas):
    draw_sky(c)
    draw_pot(c)
    big = font("Lalezar-Regular.ttf", 130)
    small = font("Tajawal-ExtraBold.ttf", 46)
    c.rect((170, 470, 420, 720), r=30, fill=WHITE)
    c.rect((170, 470, 420, 540), r=30, fill=(226, 58, 52))
    c.rect((170, 510, 420, 540), fill=(226, 58, 52))
    c.text((295, 630), "٢", big, INK)
    c.text((295, 505), "يومان", small, WHITE)
    c.text((760, 560), "؟", font("Lalezar-Regular.ttf", 220), (120, 110, 150))


def scene_sprout(c: Canvas):
    draw_sky(c)
    soil = draw_pot(c)
    draw_plant(c, soil - 4, 110, leaves=2)
    for x, y, r in ((420, 700, 26), (670, 680, 30)):
        sparkle(c, x, y, r)


def scene_grow(c: Canvas):
    draw_sky(c)
    soil = draw_pot(c)
    draw_plant(c, soil - 4, 380, leaves=6, flowers=2)


def scene_fruit(c: Canvas):
    draw_sky(c)
    soil = draw_pot(c)
    draw_plant(c, soil - 4, 500, leaves=8, flowers=3, fruits=3)
    for x, y, r in ((250, 560, 28), (830, 640, 24), (300, 820, 20)):
        sparkle(c, x, y, r)


SCENES = {name[6:]: fn for name, fn in globals().items() if name.startswith("scene_")}


# ---------------------------------------------------------------- الشخصيات
def draw_character(c: Canvas, who: str, active: bool):
    ch = CHARACTERS[who]
    cx = 830 if ch["side"] == "right" else 250
    k = 1.0 if active else 0.82
    base = 1430
    hy = base - 175 * k
    if active:
        c.ellipse((cx - 175, hy - 150, cx + 175, base + 30), fill=(*ch["color"], 45))
    skin = (247, 206, 170)
    # الجسم
    c.rect((cx - 120 * k, base - 85 * k, cx + 120 * k, base + 40), r=60 * k, fill=ch["color"])
    # الرأس
    r = 95 * k
    if who == "mirai":
        c.ellipse((cx - r - 12 * k, hy - r - 8 * k, cx + r + 12 * k, hy + r * 0.9), fill=(60, 40, 50))
        for sx in (-1, 1):
            c.ellipse((cx + sx * 88 * k - 38 * k, hy - 95 * k - 30 * k, cx + sx * 88 * k + 38 * k, hy - 95 * k + 38 * k),
                      fill=(60, 40, 50))
    c.ellipse((cx - r, hy - r, cx + r, hy + r), fill=skin)
    if who == "sanad":
        c.d.chord(c.s(cx - r - 4, hy - r - 8, cx + r + 4, hy + r * 0.5), 180, 360, fill=(50, 40, 40))
        c.rect((cx - r - 6, hy - 40 * k, cx + r * 0.1, hy - 18 * k), r=10, fill=(50, 40, 40))
    else:
        c.d.chord(c.s(cx - r - 2, hy - r - 6, cx + r + 2, hy + r * 0.35), 180, 360, fill=(60, 40, 50))
        sparkle(c, cx + 62 * k, hy - 62 * k, 20 * k, (255, 150, 200))
    # الوجه
    for sx in (-1, 1):
        c.ellipse((cx + sx * 34 * k - 11 * k, hy - 2 * k, cx + sx * 34 * k + 11 * k, hy + 22 * k), fill=INK)
        c.ellipse((cx + sx * 34 * k - 4 * k, hy + 2 * k, cx + sx * 34 * k + 3 * k, hy + 9 * k), fill=WHITE)
        c.ellipse((cx + sx * 58 * k - 16 * k, hy + 32 * k, cx + sx * 58 * k + 16 * k, hy + 48 * k),
                  fill=(255, 140, 140, 120))
    if active:
        c.d.chord(c.s(cx - 24 * k, hy + 30 * k, cx + 24 * k, hy + 74 * k), 0, 180, fill=(170, 60, 70))
    else:
        c.arc((cx - 24 * k, hy + 26 * k, cx + 24 * k, hy + 62 * k), 20, 160, width=6 * k, fill=INK)
    # الاسم
    nf = font("Marhey-Bold.ttf", 44 if active else 36)
    tw = c.text_w(ch["name"], nf)
    c.rect((cx - tw / 2 - 30, base + 50, cx + tw / 2 + 30, base + 120), r=35,
           fill=ch["color"] if active else (255, 255, 255, 200))
    c.text((cx, base + 85), ch["name"], nf, WHITE if active else ch["color"])
    if not active:
        c.ellipse((cx - 130, hy - 130, cx + 130, base + 45), fill=(255, 255, 255, 70))


# ---------------------------------------------------------------- الإطارات
def header(c: Canvas, title: str):
    c.text((540, 120), title, font("Lalezar-Regular.ttf", 96), WHITE, stroke=0)
    c.text((540, 205), "ميراي سند", font("Marhey-Bold.ttf", 40), (255, 236, 170))


def frame_line(ep: dict, line: dict) -> Image.Image:
    c = Canvas()
    vertical_gradient(c, (0, 0, W, H), (54, 120, 84), (24, 62, 52))
    header(c, ep["title"])
    SCENES[line["scene"]](c)
    for who in CHARACTERS:
        if who != line["speaker"]:
            draw_character(c, who, False)
    draw_character(c, line["speaker"], True)
    # فقاعة الترجمة
    ch = CHARACTERS[line["speaker"]]
    f = font("Tajawal-ExtraBold.ttf", 54)
    rows = wrap(c, line["text"], f, 920)
    lh = 78
    box_h = lh * len(rows) + 56
    top = min(1640, H - 40 - box_h)
    c.rect((50, top, W - 50, top + box_h), r=40, fill=(255, 255, 255, 245), outline=ch["color"], width=6)
    tail_x = 830 if ch["side"] == "right" else 250
    c.poly([(tail_x - 30, top + 3), (tail_x + 30, top + 3), (tail_x, top - 40)], fill=ch["color"])
    for i, row in enumerate(rows):
        c.text((540, top + 28 + lh * i + lh / 2), row, f, INK)
    return c.final()


def frame_title(ep: dict) -> Image.Image:
    c = Canvas()
    vertical_gradient(c, (0, 0, W, H), (70, 160, 100), (24, 62, 52))
    c.text((540, 370), "ميراي سند", font("Marhey-Bold.ttf", 70), (255, 236, 170))
    c.text((540, 580), ep["title"], font("Lalezar-Regular.ttf", 210), WHITE)
    c.text((540, 735), ep.get("subtitle", ""), font("Tajawal-Bold.ttf", 50), (220, 240, 225))
    soil = draw_pot(c, base=1180)
    draw_plant(c, soil - 4, 120, leaves=4)
    draw_character(c, "sanad", True)
    draw_character(c, "mirai", True)
    return c.final()


def frame_outro(ep: dict) -> Image.Image:
    c = Canvas()
    vertical_gradient(c, (0, 0, W, H), (54, 120, 84), (24, 62, 52))
    scene_fruit(c)
    c.text((540, 120), ep["title"], font("Lalezar-Regular.ttf", 96), WHITE)
    draw_character(c, "sanad", True)
    draw_character(c, "mirai", True)
    f = font("Lalezar-Regular.ttf", 86)
    c.rect((60, 1640, W - 60, 1840), r=50, fill=(255, 205, 70))
    c.text((540, 1742), ep["outro"], f, INK)
    return c.final()


# ------------------------------------------------------------------- الصوت
async def edge_tts(text: str, voice: str, out: Path) -> None:
    import edge_tts as et
    await et.Communicate(text, voice, rate="-4%").save(str(out))


EDGE_OK = True


def tts(text: str, who: str, out: Path, engine: str) -> Path:
    global EDGE_OK
    ch = CHARACTERS[who]
    if engine == "edge" or (engine == "auto" and EDGE_OK):
        mp3 = out.with_suffix(".mp3")
        try:
            asyncio.run(edge_tts(text, ch["edge"], mp3))
            if mp3.stat().st_size > 1000:
                run(["ffmpeg", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "1", str(out)])
                return out
        except Exception as e:  # الشبكة أو الخدمة غير متاحة
            if engine == "edge":
                raise
            EDGE_OK = False
            log(f"edge-tts غير متاح ({type(e).__name__})، سأستخدم Piper المحلي لبقية الجمل")
    raw = out.with_suffix(".piper.wav")
    subprocess.run([str(Path(sys.executable).parent / "piper"), "-m", str(PIPER_MODEL), "-f", str(raw),
                    "--length-scale", "1.05"], input=text, text=True, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    p = ch["piper_pitch"]
    # صوت ميراي: نرفع الطبقة دون تغيير السرعة
    af = f"asetrate=22050*{p},aresample=44100,atempo={1 / p:.4f}" if p != 1.0 else "aresample=44100"
    run(["ffmpeg", "-y", "-i", str(raw), "-af", af, "-ac", "1", str(out)])
    return out


# ------------------------------------------------------------------- التركيب
def segment(img: Path, seconds: float, out: Path, zoom: bool = True) -> float:
    frames = max(1, round(seconds * FPS))
    vf = (f"scale={W * 2}:{H * 2},zoompan=z='1+0.035*on/{frames}':x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}") if zoom else f"fps={FPS}"
    run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-vf", vf, "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(out)])
    return frames / FPS


def pad_audio(src: Path | None, seconds: float, out: Path) -> None:
    if src is None:
        run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{seconds:.3f}", str(out)])
    else:
        run(["ffmpeg", "-y", "-i", str(src), "-af", f"apad,atrim=0:{seconds:.3f}", "-ar", "44100", "-ac", "1", str(out)])


def render(ep_file: Path, engine: str) -> Path:
    ep = tomllib.loads(ep_file.read_text(encoding="utf-8"))
    work = BUILD / ep["id"]
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    log(f"الحلقة: {ep['title']} ({len(ep['lines'])} جملة)")

    parts: list[tuple[Path, Path]] = []  # (فيديو, صوت)

    def add(img: Image.Image, voice: Path | None, seconds: float, name: str):
        png = work / f"{name}.png"
        img.save(png)
        exact = segment(png, seconds, work / f"{name}.mp4")
        pad_audio(voice, exact, work / f"{name}.wav")
        parts.append((work / f"{name}.mp4", work / f"{name}.wav"))

    add(frame_title(ep), None, 2.6, "000-title")
    for i, line in enumerate(ep["lines"], 1):
        voice = tts(line["text"], line["speaker"], work / f"{i:03d}-voice.wav", engine)
        add(frame_line(ep, line), voice, ffprobe_duration(voice) + GAP, f"{i:03d}")
        log(f"  {i}/{len(ep['lines'])} {CHARACTERS[line['speaker']]['name']}")
    outro_voice = tts(ep["outro"], "sanad", work / "999-voice.wav", engine)
    add(frame_outro(ep), outro_voice, ffprobe_duration(outro_voice) + 1.8, "999-outro")

    for kind, idx in (("video", 0), ("audio", 1)):
        (work / f"{kind}.txt").write_text("".join(f"file '{p[idx].name}'\n" for p in parts))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "video.txt"), "-c", "copy",
         str(work / "video.mp4")])
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(work / "audio.txt"), str(work / "voice.wav")])

    total = ffprobe_duration(work / "video.mp4")
    songs = sorted(SONGS.glob("*.mp3")) if SONGS.exists() else []
    OUTPUT.mkdir(exist_ok=True)
    out = OUTPUT / f"{ep['id']}.mp4"
    # تنظيف الصوت وتوحيد مستواه (loudnorm) ثم مزج موسيقى هادئة
    voice_chain = "[1:a]highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11[v]"
    if songs:
        song = songs[sum(map(ord, ep["id"])) % len(songs)]
        fc = (f"{voice_chain};[2:a]aloop=-1:size=2e9,atrim=0:{total:.3f},volume=0.09,"
              f"afade=t=out:st={max(total - 2, 0):.3f}:d=2[m];[v][m]amix=inputs=2:normalize=0[a]")
        inputs = ["-i", str(work / "video.mp4"), "-i", str(work / "voice.wav"), "-i", str(song)]
    else:
        fc = voice_chain.replace("[v]", "[a]")
        inputs = ["-i", str(work / "video.mp4"), "-i", str(work / "voice.wav")]
    run(["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-t", f"{total:.3f}",
         "-movflags", "+faststart", str(out)])
    (work / "lines.json").write_text(json.dumps(ep["lines"], ensure_ascii=False, indent=1))
    log(f"✓ {out.relative_to(ROOT)} ({total:.1f} ثانية)")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="توليد حلقات ميراي وسند الحوارية")
    p.add_argument("episodes", nargs="*", help="أسماء الحلقات (الافتراضي: كل ملفات dialogues/)")
    p.add_argument("--tts", choices=["auto", "edge", "piper"], default="auto")
    args = p.parse_args()
    if not features.check("raqm"):
        sys.exit("Pillow بدون raqm: الحروف العربية ستتقطع. ثبّت libraqm أو libfribidi.")
    files = sorted(DIALOGUES.glob("*.toml"))
    if args.episodes:
        files = [DIALOGUES / f"{e}.toml" for e in args.episodes]
        missing = [f.stem for f in files if not f.exists()]
        if missing:
            sys.exit(f"حلقات غير موجودة: {', '.join(missing)}")
    for f in files:
        render(f, args.tts)


if __name__ == "__main__":
    main()
