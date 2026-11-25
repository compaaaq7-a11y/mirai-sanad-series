"""صوت وتركيب حلقة «سند وميراي والفرخ الصغير» ثلاثية الأبعاد.

    python blender/ep06_finish.py audio    # التعليق (edge-tts) + زقزقة + موسيقى
    python blender/ep06_finish.py video    # دمج الإطارات مع الصوت في mp4

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
BUILD = ROOT / "build" / "ep06"
SR = 44100
DUR = 30.0
VOICE = "ar-IQ-RanaNeural"
RATE = "-8%"

# كل جملة تبدأ مع مشهدها (بالثواني)
LINES = [
    (0.9, "سمع سند وميراي زقزقةً تحت الشجرة."),
    (6.3, "كان فرخٌ صغير قد سقط من عشّه، وقطةٌ تستعدّ للانقضاض عليه!"),
    (12.4, "دحرجت ميراي كرة الصوف، فركضت القطة خلفها."),
    (16.6, "وحمل سند الفرخ برفق وأعاده إلى عشّه."),
    (23.4, "وحين عادت أمّه، زقزق كأنّه يقول لهما: شكرًا!"),
]
CHICK_CHIRPS = [0.6, 1.4, 2.2, 3.4, 4.6, 23.6, 24.0, 24.4, 24.8, 29.0, 29.4]
MOM_CHIRPS = [23.3, 24.2]


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
async def tts_all(out_dir: Path):
    import edge_tts
    for i, (_, text) in enumerate(LINES):
        await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(out_dir / f"line{i}.mp3"))


def audio(args):
    BUILD.mkdir(parents=True, exist_ok=True)
    n = int(SR * DUR)
    voice = np.zeros(n)
    spans = []
    if not args.no_voice:
        asyncio.run(tts_all(BUILD))
    for i, (start, text) in enumerate(LINES):
        p = BUILD / f"line{i}.mp3"
        if args.no_voice or not p.exists():
            spans.append((start, start + 3.5, text))
            continue
        clip = read_audio(p)
        i0 = int(start * SR)
        voice[i0:i0 + len(clip)] += clip[: n - i0]
        end = start + len(clip) / SR
        spans.append((start, end, text))
        nxt = LINES[i + 1][0] if i + 1 < len(LINES) else DUR
        if end > nxt + 0.05:
            print(f"تحذير: الجملة {i + 1} تتداخل مع التالية ({end:.2f} > {nxt})")
    rng = np.random.default_rng(3)
    birds = np.zeros(n)
    for t in CHICK_CHIRPS:
        c = chirp(1.0, rng)
        i0 = int(t * SR)
        birds[i0:i0 + len(c)] += c[: n - i0]
    for t in MOM_CHIRPS:
        c = chirp(0.72, rng) * 0.8
        i0 = int(t * SR)
        birds[i0:i0 + len(c)] += c[: n - i0]
    mus = music()
    # خفض الموسيقى أثناء الكلام
    duck = np.ones(n)
    for s, e, _ in spans:
        duck[int(max(0, s - 0.2) * SR):int(min(DUR, e + 0.3) * SR)] = 0.55
    k = int(SR * 0.25)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    vpk = np.abs(voice).max()
    if vpk > 0:
        voice = voice / vpk * 0.9
    left = voice + 0.16 * mus * duck + 0.35 * birds
    right = voice + 0.16 * mus * duck + 0.35 * np.roll(birds, int(SR * 0.004))
    stereo = np.stack([left, right], axis=1)
    stereo /= max(1.0, np.abs(stereo).max() / 0.95)
    write_wav(BUILD / "audio.wav", stereo)

    (BUILD / "spans.json").write_text(json.dumps(spans, ensure_ascii=False, indent=1), encoding="utf-8")
    print("تم: build/ep06/audio.wav")


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
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audio")
    a.add_argument("--no-voice", action="store_true", help="بدون تعليق (للتجربة بلا إنترنت)")
    a.set_defaults(func=audio)
    v = sub.add_parser("video")
    v.add_argument("--frames", default=str(BUILD / "frames"))
    v.add_argument("--out", default=str(ROOT / "output" / "ep06-baby-bird-3d.mp4"))
    v.add_argument("--start", type=int, default=1, help="رقم أول إطار")
    v.set_defaults(func=video)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
