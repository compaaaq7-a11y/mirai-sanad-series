"""صوت وتركيب حلقات سند وميراي ثلاثية الأبعاد (ep06، ep07).

    python blender/finish.py --ep ep07 audio    # التعليق (edge-tts) + زقزقة + مؤثرات + موسيقى
    python blender/finish.py --ep ep07 video    # دمج الإطارات مع الصوت في mp4

المتطلبات: ffmpeg، numpy، edge-tts (لخطوة audio فقط؛ --no-voice للتجربة بدون إنترنت).
"""

import argparse
import asyncio
import json
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SR = 44100
DUR = 30.0
VOICE = "ar-IQ-RanaNeural"
RATE = "-8%"

# إعدادات كل حلقة: الجمل (تبدأ مع مشهدها بالثواني) والمؤثرات الصوتية
EPISODES = {
    "ep06": dict(
        out="ep06-baby-bird-3d.mp4",
        lines=[
            (0.9, "سمع سند وميراي زقزقةً تحت الشجرة."),
            (6.3, "كان فرخٌ صغير قد سقط من عشّه، وقطةٌ تستعدّ للانقضاض عليه!"),
            (12.4, "دحرجت ميراي كرة الصوف، فركضت القطة خلفها."),
            (16.6, "وحمل سند الفرخ برفق وأعاده إلى عشّه."),
            (23.4, "وحين عادت أمّه، زقزق كأنّه يقول لهما: شكرًا!"),
        ],
        chick=[0.6, 1.4, 2.2, 3.4, 4.6, 23.6, 24.0, 24.4, 24.8, 29.0, 29.4],
        mom=[23.3, 24.2],
    ),
    "ep07": dict(
        out="ep07-first-flight-3d.mp4",
        lines=[
            (0.6, "بعد أيام، عاد سند وميراي إلى الشجرة."),
            (5.0, "كان الفرخ قد كبر، وحان وقت رحلته الأولى."),
            (9.3, "رفرف قليلًا، ثم قفز إلى غصن قريب."),
            (14.2, "حاول مرةً أخرى… وإذا به يطير!"),
            (23.0, "ضحك سند وصفّقت ميراي، وطار العصفور بجانب أمّه."),
        ],
        chick=[0.3, 4.0, 4.7, 5.3, 10.5, 21.5, 22.0, 22.5, 27.0, 28.2],
        mom=[6.3, 7.1, 14.4, 15.0, 26.4],
        flaps=[(7.9, 8.6, 0.6), (9.5, 10.4, 1.0), (15.3, 15.9, 0.6), (15.9, 21.1, 0.8)],
        rustle=(0.0, 3.5),
        swell=(16.5, 22.0),
        claps=[11.0, 11.5, 12.0],
    ),
    "part3": dict(
        out="part3-stuck-cat-3d.mp4",
        lines=[
            (0.5, "في صباحٍ مشمس، سمع سند وميراي زقزقةً عالية."),
            (5.0, "كانت القطة قد تسلّقت الشجرة، ولم تستطع النزول!"),
            (10.4, "أحضر سند صندوقًا، ونادتها ميراي بكرة الصوف."),
            (16.4, "قفزت القطة بحذر… فالتقطها سند بين ذراعيه."),
            (23.2, "ومنذ ذلك اليوم، صار الجميع أصدقاء في الحديقة."),
        ],
        chick=[0.3, 0.9, 1.5, 2.1, 2.7, 3.3, 3.9, 18.6, 19.0, 25.5, 26.0, 28.6],
        mom=[0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 18.8, 26.3],
        flaps=[(0.0, 4.8, 0.5), (10.0, 12.8, 0.5)],
        meows=[6.2, 7.6, 9.0, 17.2],
        drag=(11.5, 13.4),
        swell=(17.8, 22.5),
        claps=[24.2, 24.46, 24.72, 24.98, 25.24, 25.5],
    ),
}
CFG = EPISODES["ep06"]
BUILD = ROOT / "build" / "ep06"


def run(cmd):
    print("$", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run([str(c) for c in cmd], check=True)


def read_audio(path: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, stdout=subprocess.PIPE).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def write_wav(path: Path, stereo: np.ndarray):
    data = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


# ------------------------------------------------------------ أصوات مُولَّدة
def env(n, attack=0.005, release=0.05):
    t = np.arange(n) / SR
    e = np.minimum(1, t / attack) * np.exp(-t / release)
    return e


def chirp(pitch=1.0, rng=None):
    """زقزقة فرخ: مقطعان أو ثلاثة صاعدة."""
    rng = rng or np.random.default_rng()
    out = []
    for _ in range(rng.integers(2, 4)):
        n = int(SR * rng.uniform(0.05, 0.08))
        t = np.arange(n) / SR
        f0, f1 = 3200 * pitch * rng.uniform(0.95, 1.05), 4800 * pitch * rng.uniform(0.95, 1.05)
        f = f0 + (f1 - f0) * (t / t[-1]) ** 0.7
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = np.sin(ph) + 0.25 * np.sin(2 * ph)
        a = np.clip(np.sin(np.pi * t / t[-1]), 0, 1) ** 1.5
        out += [s * a, np.zeros(int(SR * rng.uniform(0.03, 0.06)))]
    return np.concatenate(out) * 0.5


def pluck(freq, dur, rng=None):
    """وتر منقور (Karplus-Strong) بصوت يشبه الأوكوليلي."""
    rng = rng or np.random.default_rng(1)
    n = int(SR * dur)
    period = max(2, int(SR / freq))
    buf = rng.uniform(-1, 1, period)
    out = np.empty(n)
    decay = 0.996
    for i in range(n):
        out[i] = buf[i % period]
        j = (i + 1) % period
        buf[i % period] = decay * 0.5 * (buf[i % period] + buf[j])
    return out * env(n, 0.002, dur * 0.6)


def bell(freq, dur):
    n = int(SR * dur)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 6)
    return s * env(n, 0.003, 0.5)


def music() -> np.ndarray:
    """موسيقى مرحة خافتة: أوكوليلي على C-G-Am-F مع لحن أجراس."""
    note = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [[60, 64, 67, 72], [55, 62, 67, 71], [57, 64, 69, 72], [53, 60, 65, 69]]
    bpm = 104
    eighth = 60 / bpm / 2
    out = np.zeros(int(SR * (DUR + 2)))
    t = 0.0
    bar = 0
    melody = [76, 79, 81, 79, 76, 74, 72, 74, 76, 74, 72, 67, 69, 72, 74, 72]
    mi = 0
    while t < DUR:
        ch = chords[bar % 4]
        for k, m in enumerate([ch[0], ch[2], ch[1], ch[3], ch[2], ch[1], ch[3], ch[2]]):
            tt = t + k * eighth
            if tt >= DUR:
                break
            s = pluck(note(m), 0.9) * (0.5 if k else 0.7)
            i = int(tt * SR)
            out[i:i + len(s)] += s[: len(out) - i]
        bass = pluck(note(ch[0] - 12), 1.6) * 0.6
        i = int(t * SR)
        out[i:i + len(bass)] += bass[: len(out) - i]
        for k in (0, 2, 3, 6):
            tt = t + k * eighth
            if tt < DUR - 1 and bar % 2 == 0 or k in (0, 3):
                b = bell(note(melody[mi % len(melody)]), 1.0) * 0.18
                mi += 1
                i = int(tt * SR)
                out[i:i + len(b)] += b[: len(out) - i]
        t += 8 * eighth
        bar += 1
    out = out[: int(SR * DUR)]
    fade = np.ones_like(out)
    nf = int(SR * 2.5)
    fade[-nf:] = np.linspace(1, 0, nf)
    fade[: int(SR * 0.5)] = np.linspace(0, 1, int(SR * 0.5))
    return out / (np.abs(out).max() + 1e-9) * fade


# ------------------------------------------------------------ التعليق
def noise_band(n, lo, hi, rng):
    """ضوضاء مفلترة بين ترددين (لحفيف الأوراق ورفرفة الأجنحة)."""
    x = rng.standard_normal(n)
    spec = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    y = np.fft.irfft(spec, n)
    return y / (np.abs(y).max() + 1e-9)


def flutter(t0, t1, n, rng, gain=1.0):
    """رفرفة: نبضات هوائية سريعة."""
    out = np.zeros(n)
    t = t0
    while t < t1:
        m = int(SR * 0.07)
        b = noise_band(m, 300, 2500, rng) * np.sin(np.linspace(0, np.pi, m)) ** 2
        i = int(t * SR)
        out[i:i + m] += b[: n - i] * gain
        t += rng.uniform(0.1, 0.14)
    return out


def meow(rng):
    """مواء قطة صغيرة: نغمة تصعد ثم تنزل مع اهتزاز خفيف."""
    n = int(SR * 0.65)
    t = np.arange(n) / SR
    f = 520 + 420 * np.sin(np.pi * t / t[-1]) ** 1.5 - 120 * (t / t[-1])
    f *= 1 + 0.012 * np.sin(2 * np.pi * 6 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.25 * np.sin(3 * ph) + 0.12 * np.sin(4 * ph)
    a = np.clip(np.sin(np.pi * t / t[-1]), 0, 1) ** 0.8
    return s * a / 1.9 * rng.uniform(0.85, 1.0)


def footstep(rng, soft=1.0):
    """خطوة خفيفة على العشب: حفيف قصير ناعم مع نقرة منخفضة خافتة."""
    n = int(SR * 0.09)
    t = np.arange(n) / SR
    rustle = noise_band(n, 900, 4500, rng) * np.exp(-t / 0.025) * 0.5
    thump = np.sin(2 * np.pi * rng.uniform(85, 110) * t) * np.exp(-t / 0.018) * 0.6
    return (rustle + thump) * soft * rng.uniform(0.7, 1.0)


def clap(rng):
    m = int(SR * 0.06)
    return noise_band(m, 800, 6000, rng) * np.exp(-np.arange(m) / (SR * 0.012))


# تشكيل الأسماء ليُنطق «ميراي» كاملاً لا «ميري»
SAY = {"ميراي": "مِيرَاايْ"}


async def tts_all(out_dir: Path):
    import os
    import edge_tts
    kw = {}
    ca = os.environ.get("SSL_CERT_FILE")
    if ca:  # خلف وكيل HTTPS بشهادة خاصة
        import ssl
        import edge_tts.communicate as cm
        cm._SSL_CTX = ssl.create_default_context(cafile=ca)
        kw["proxy"] = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    for i, (_, text) in enumerate(CFG["lines"]):
        for k, v in SAY.items():
            text = text.replace(k, v)
        await edge_tts.Communicate(text, VOICE, rate=RATE, **kw).save(str(out_dir / f"line{i}.mp3"))


def audio(args):
    BUILD.mkdir(parents=True, exist_ok=True)
    n = int(SR * DUR)
    voice = np.zeros(n)
    spans = []
    if not args.no_voice and not (args.keep_voice and (BUILD / "line0.mp3").exists()):
        asyncio.run(tts_all(BUILD))
    prev_end = 0.0
    for i, (start, text) in enumerate(CFG["lines"]):
        p = BUILD / f"line{i}.mp3"
        if args.no_voice or not p.exists():
            spans.append((start, start + 3.5, text))
            continue
        clip = read_audio(p)
        # قصّ الصمت من البداية والنهاية، ومنع تداخل جملة مع التي قبلها
        loud = np.nonzero(np.abs(clip) > 0.01)[0]
        if len(loud):
            clip = clip[max(0, loud[0] - int(0.03 * SR)):loud[-1] + int(0.08 * SR)]
        if start < prev_end + 0.15:
            print(f"الجملة {i + 1}: تأخير من {start:.2f} إلى {prev_end + 0.15:.2f} لتجنّب التداخل")
            start = prev_end + 0.15
        i0 = int(start * SR)
        voice[i0:i0 + len(clip)] += clip[: n - i0]
        end = start + len(clip) / SR
        prev_end = end
        spans.append((start, end, text))
        nxt = CFG["lines"][i + 1][0] if i + 1 < len(CFG["lines"]) else DUR
        if end > nxt + 0.05:
            print(f"تحذير: الجملة {i + 1} تتداخل مع التالية ({end:.2f} > {nxt})")
    rng = np.random.default_rng(3)
    birds = np.zeros(n)
    for t in CFG["chick"]:
        c = chirp(1.0, rng)
        i0 = int(t * SR)
        birds[i0:i0 + len(c)] += c[: n - i0]
    for t in CFG.get("mom", []):
        c = chirp(0.72, rng) * 0.8
        i0 = int(t * SR)
        birds[i0:i0 + len(c)] += c[: n - i0]
    fx = np.zeros(n)
    for t0, t1, g in CFG.get("flaps", []):
        fx += flutter(t0, t1, n, rng, 0.35 * g)
    if "rustle" in CFG:
        r0, r1 = CFG["rustle"]
        m = int((r1 - r0) * SR)
        lv = noise_band(m, 1500, 7000, rng) * 0.12
        lv *= np.interp(np.arange(m), [0, m * 0.3, m * 0.7, m - 1], [0, 1, 0.6, 0]) * (0.6 + 0.4 * np.sin(np.arange(m) / SR * 7))
        fx[int(r0 * SR):int(r0 * SR) + m] += lv
    ev = BUILD / "events.json"
    if ev.exists():  # خطوات المشي والهبوط من القفزات، مستخرجة من حركة المشهد
        events = json.loads(ev.read_text(encoding="utf-8"))
        for t in events.get("steps", []):
            c = footstep(rng) * 0.09
            i0 = int(t * SR)
            fx[i0:i0 + len(c)] += c[: max(0, n - i0)]
        for t in events.get("lands", []):
            c = footstep(rng, 1.3) * 0.11
            i0 = int(t * SR)
            fx[i0:i0 + len(c)] += c[: max(0, n - i0)]
    for t in CFG.get("meows", []):
        c = meow(rng) * 0.45
        i0 = int(t * SR)
        fx[i0:i0 + len(c)] += c[: n - i0]
    if "drag" in CFG:  # جرّ الصندوق على العشب
        d0, d1 = CFG["drag"]
        m = int((d1 - d0) * SR)
        dr = noise_band(m, 250, 1400, rng) * 0.06
        dr *= np.interp(np.arange(m), [0, m * 0.1, m * 0.9, m - 1], [0, 1, 1, 0]) * (0.7 + 0.3 * np.sin(np.arange(m) / SR * 11))
        fx[int(d0 * SR):int(d0 * SR) + m] += dr
    for t in CFG.get("claps", []):
        c = clap(rng) * 0.4
        i0 = int(t * SR)
        fx[i0:i0 + len(c)] += c
    mus = music()
    # خفض الموسيقى أثناء الكلام
    duck = np.ones(n)
    for s, e, _ in spans:
        duck[int(max(0, s - 0.2) * SR):int(min(DUR, e + 0.3) * SR)] = 0.55
    if "swell" in CFG:  # الموسيقى ترتفع لحظة النجاح
        s0, s1 = CFG["swell"]
        duck[int(s0 * SR):int(s1 * SR)] = np.maximum(duck[int(s0 * SR):int(s1 * SR)], 1.9)
    k = int(SR * 0.25)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    vpk = np.abs(voice).max()
    if vpk > 0:
        voice = voice / vpk * 0.9
    left = voice + 0.16 * mus * duck + 0.35 * birds + fx
    right = voice + 0.16 * mus * duck + 0.35 * np.roll(birds, int(SR * 0.004)) + np.roll(fx, int(SR * 0.003))
    stereo = np.stack([left, right], axis=1)
    stereo /= max(1.0, np.abs(stereo).max() / 0.95)
    write_wav(BUILD / "audio.wav", stereo)

    (BUILD / "spans.json").write_text(json.dumps(spans, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"تم: {BUILD / 'audio.wav'}")


def video(args):
    frames = Path(args.frames).resolve()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", "24", "-start_number", str(args.start), "-i", frames / "f_%04d.png"]
    has_audio = (BUILD / "audio.wav").exists()
    if has_audio:
        cmd += ["-i", BUILD / "audio.wav", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
            "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-movflags", "+faststart", out]
    run(cmd)
    print(f"تم: {out}")


def main():
    global CFG, BUILD
    ap = argparse.ArgumentParser()
    ap.add_argument("--ep", default="ep06", choices=sorted(EPISODES), help="الحلقة")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audio")
    a.add_argument("--no-voice", action="store_true", help="بدون تعليق (للتجربة بلا إنترنت)")
    a.add_argument("--keep-voice", action="store_true", help="استخدام ملفات التعليق الموجودة بدل توليدها من جديد")
    a.set_defaults(func=audio)
    v = sub.add_parser("video")
    v.add_argument("--frames")
    v.add_argument("--out")
    v.add_argument("--start", type=int, default=1, help="رقم أول إطار")
    v.set_defaults(func=video)
    args = ap.parse_args()
    CFG = EPISODES[args.ep]
    BUILD = ROOT / "build" / args.ep
    if args.cmd == "video":
        args.frames = args.frames or str(BUILD / "frames")
        args.out = args.out or str(ROOT / "output" / CFG["out"])
    args.func(args)


if __name__ == "__main__":
    main()
