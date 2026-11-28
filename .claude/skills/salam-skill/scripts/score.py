#!/usr/bin/env python3
"""مؤلّف موسيقى ومؤثرات خاص بكل مقطع (مجاني، بلا حقوق، بلا إنترنت) — قاعدة: لا تكرّر موسيقى إعلان سابق.

  score.py score.json -o soundtrack.wav

score.json:
{ "duration": 28.7, "bpm": 112, "key": "D",            ← غيّر المقام والسرعة والآلات لكل مقطع
  "sections": [ {"from":0, "to":8.6, "style":"pizz"}, {"from":8.6,"to":11.2,"style":"roll"},
                {"from":11.2,"to":15,"style":"rest"}, {"from":15,"to":19.7,"style":"glock"},
                {"from":21.7,"to":28.7,"style":"party"} ],
  "events": [ ["tap",4.22], ["kick",11.22], ["whoosh_up",11.25], ["boing",13.42], ["ding",17.3],
              ["swish",21.7], ["crowd",21.8,4], ["whistle",22.0], ["wah",5.2], ["rise",7.1,1.5], ["steps",8.6,1.3,0.16] ] }

الأنماط: pizz (أوتار نقر + باص + طبل خفيف)، glock (جرس تفكير هادئ)، roll (قرع طبل يتصاعد)، rest (صمت/هواء)،
party (احتفال: تصفيق + باص + تآلفات نحاسية)، march (مارش طبول)، lofi (بيانو كهربائي بطيء).
المؤثرات: tap kick whoosh whoosh_up boing ding swish crowd whistle wah rise steps pop bounce.
"""
import argparse, json, wave
import numpy as np

SR = 44100
NOTE = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}
rng = np.random.default_rng(7)


def hz(semi_from_a4):
    return 440.0 * 2 ** (semi_from_a4 / 12)


def tt(d):
    return np.arange(int(d * SR)) / SR


def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e


def add(buf, sig, t0, g=1.0):
    i = int(t0 * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(len(buf), i + len(sig))
    buf[i:j] += g * sig[:j - i]


def pluck(f, d=0.5):   # Karplus-Strong
    n = int(d * SR); p = max(2, int(SR / f))
    x = rng.uniform(-1, 1, p); out = np.zeros(n)
    for k in range(n):
        out[k] = x[k % p]
        x[k % p] = 0.5 * (x[k % p] + x[(k + 1) % p]) * 0.996
    return out * 0.6


def bell(f, d=1.2):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.76 * t) + 0.15 * np.sin(2 * np.pi * f * 5.4 * t)) * np.exp(-t * 3.2) * 0.35


def epiano(f, d=1.0):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t + 0.8 * np.sin(2 * np.pi * f * t) * np.exp(-t * 4))) * env(len(t), 0.01, 0.6) * 0.3


def brass(f, d=0.4):
    t = tt(d); s = np.zeros_like(t)
    for h in range(1, 7):
        s += np.sin(2 * np.pi * f * h * t) / h ** 1.1
    a = np.minimum(1, t / 0.04) * np.exp(-t * 2.5)
    return s * a * 0.18


def bass(f, d=0.4):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * env(len(t), 0.004, d * 0.6) * 0.5


def kickdrum(g=1.0):
    t = tt(0.35)
    return np.sin(2 * np.pi * (45 * t + 90 / 30 * (1 - np.exp(-30 * t)))) * np.exp(-t * 9) * 0.9 * g


def noise(d):
    return rng.uniform(-1, 1, int(d * SR))


def hp(x, a=0.9):   # مرشح تمرير عالٍ بسيط
    y = np.zeros_like(x); p = 0
    for i in range(1, len(x)):
        p = a * (p + x[i] - x[i - 1]); y[i] = p
    return y


def lp(x, a=0.2):
    y = np.zeros_like(x); p = 0
    for i in range(len(x)):
        p += a * (x[i] - p); y[i] = p
    return y


SN = None
def snare(g=1.0):
    global SN
    if SN is None:
        t = tt(0.22)
        SN = (hp(noise(0.22), 0.7) * np.exp(-t * 18) * 0.5 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * 0.4)
    return SN * g


HAT = None
def hat(g=1.0):
    global HAT
    if HAT is None:
        HAT = hp(noise(0.05), 0.95) * np.exp(-tt(0.05) * 70) * 0.25
    return HAT * g


CLAP = None
def clap(g=1.0):
    global CLAP
    if CLAP is None:
        t = tt(0.25); n = hp(noise(0.25), 0.8)
        e = np.exp(-t * 30) + 0.7 * np.exp(-np.maximum(0, t - 0.012) * 30) * (t > 0.012) + 0.5 * np.exp(-np.maximum(0, t - 0.024) * 25) * (t > 0.024)
        CLAP = n * e * 0.35
    return CLAP * g


def scale(key):
    r = NOTE[key] - 9   # بالنسبة لـ A
    return [r + s for s in (0, 2, 4, 5, 7, 9, 11)]


def section(buf, s, bpm, key):
    a, b, st = s['from'], s['to'], s['style']
    beat = 60 / bpm; sc = scale(key); g = s.get('gain', 1.0)
    n_beats = int((b - a) / beat)
    prog = [0, 3, 4, 0] if st != 'lofi' else [0, 5, 3, 4]   # I IV V I / I vi IV V
    for k in range(n_beats):
        t = a + k * beat; bar = k // 4; deg = prog[bar % 4]; root = sc[deg] - 24
        if st == 'pizz':
            add(buf, bass(hz(root), beat * 0.9), t, 0.5 * g) if k % 2 == 0 else None
            for h, off in ((0, 0), (2, 0.5)):
                mel = sc[(deg + [0, 2, 4, 2, 5, 4, 2, 1][(k * 2 + h // 2) % 8]) % 7] + 12
                add(buf, pluck(hz(mel), 0.45), t + off * beat, 0.32 * g)
            add(buf, hat(), t + beat / 2, 0.6 * g)
            if k % 4 == 2: add(buf, snare(0.35), t, g)
        elif st == 'glock':
            for h in range(2):
                mel = sc[(deg + [4, 2, 0, 2][(k * 2 + h) % 4]) % 7] + 24
                add(buf, bell(hz(mel), 1.4), t + h * beat / 2, 0.22 * g)
            if k % 4 == 0: add(buf, epiano(hz(root + 12), beat * 4), t, 0.35 * g)
        elif st == 'lofi':
            if k % 4 == 0:
                for d in (0, 2, 4, 6):
                    add(buf, epiano(hz(sc[(deg + d) % 7] - 12 + (12 if (deg + d) >= 7 else 0)), beat * 4), t, 0.18 * g)
            add(buf, kickdrum(0.5), t, g) if k % 4 in (0, 2) else add(buf, snare(0.25), t, g)
            add(buf, hat(0.5), t + beat / 2, g)
        elif st == 'march':
            add(buf, kickdrum(0.6), t, g) if k % 2 == 0 else add(buf, snare(0.5), t, g)
            add(buf, snare(0.15), t + beat * 0.75, g)
            add(buf, bass(hz(root), beat), t, 0.4 * g)
        elif st == 'party':
            add(buf, kickdrum(0.8), t, g)
            add(buf, bass(hz(root), beat * 0.45), t + beat / 2, 0.5 * g)
            add(buf, hat(0.8), t + beat / 2, g)
            if k % 2 == 1: add(buf, clap(), t, 0.9 * g)
            if k % 2 == 0:
                for d in (0, 2, 4):
                    add(buf, brass(hz(sc[(deg + d) % 7] + (12 if (deg + d) >= 7 else 0)), beat * 0.8), t, 0.35 * g)
    if st == 'roll':   # قرع يتسارع ويعلو
        t = a
        while t < b:
            p = (t - a) / max(0.01, b - a)
            add(buf, snare(0.15 + 0.5 * p), t, g)
            t += 0.16 - 0.11 * p
        add(buf, bass(hz(sc[4] - 24), b - a), a, 0.25 * g)


def sfx(buf, name, t0, d=1.0, extra=None):
    if name == 'tap':
        t = tt(0.15); add(buf, np.sin(2 * np.pi * 140 * t) * np.exp(-t * 35) * 0.6 + hp(noise(0.15), 0.6) * np.exp(-t * 60) * 0.2, t0)
    elif name == 'kick':
        add(buf, kickdrum(1.3), t0); t = tt(0.12); add(buf, hp(noise(0.12), 0.5) * np.exp(-t * 40) * 0.5, t0)
    elif name in ('whoosh', 'whoosh_up'):
        dd = d if extra is None else extra; t = tt(dd); n = noise(dd)
        e = np.sin(np.pi * np.minimum(1, t / dd)) ** 2
        add(buf, lp(n, 0.25) * e * 0.9, t0)
        if name == 'whoosh_up':
            add(buf, np.sin(2 * np.pi * (300 * t + 900 * t * t / dd)) * e * 0.15, t0)
    elif name == 'boing':
        t = tt(0.7); f = 180 + 120 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
        add(buf, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4) * 0.55, t0); add(buf, kickdrum(0.5), t0)
    elif name == 'bounce':
        t = tt(0.18); add(buf, np.sin(2 * np.pi * 120 * t) * np.exp(-t * 28) * 0.45, t0)
    elif name == 'ding':
        add(buf, bell(hz(15), 1.6), t0, 1.6); add(buf, bell(hz(22), 1.6), t0 + 0.08, 1.0)
    elif name == 'pop':
        t = tt(0.08); add(buf, np.sin(2 * np.pi * (900 - 6000 * t) * t) * np.exp(-t * 50) * 0.4, t0)
    elif name == 'swish':   # الكرة في الشبكة
        t = tt(0.6); add(buf, hp(noise(0.6), 0.85) * np.exp(-t * 6) * (1 - np.exp(-t * 80)) * 0.6, t0)
    elif name == 'crowd':   # هتاف جمهور حقيقي الطابع: أصوات بشرية بحروف علة + تصفيق + صدى ملعب
        add(buf, crowd(d), t0)
    elif name == 'crowd_noise':   # (القديم: ضوضاء — يشبه الوشوشة، لا تستخدمه للتشجيع)
        t = tt(d); n = lp(noise(d), 0.18) * 1.6
        sw = np.minimum(1, t / 0.25) * np.minimum(1, (d - t) / 1.2)
        mod = 0.75 + 0.25 * np.sin(2 * np.pi * 3.1 * t) * np.sin(2 * np.pi * 0.7 * t)
        add(buf, n * sw * mod * 0.6, t0)
        for k in range(14):
            s = t0 + rng.uniform(0, d * 0.7); tv = tt(0.35); f = rng.uniform(380, 700)
            add(buf, np.sin(2 * np.pi * (f * tv + 150 * tv * tv)) * np.sin(np.pi * tv / 0.35) * 0.05, s)
    elif name == 'whistle':
        for k, (a, b) in enumerate(((0, 0.18), (0.26, 0.7))):
            t = tt(b - a); f = 2900 + 120 * np.sign(np.sin(2 * np.pi * 32 * t))
            add(buf, np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.01) * 0.16, t0 + a)
    elif name == 'wah':   # «وا وا وااا» حزين
        for k, f in enumerate((hz(-10), hz(-11), hz(-12), hz(-13.5))):
            dd = 0.32 if k < 3 else 0.9; t = tt(dd)
            ff = f * (1 + (0.02 * np.sin(2 * np.pi * 6 * t) if k == 3 else 0))
            s = sum(np.sin(2 * np.pi * np.cumsum(ff * h) / SR) / h for h in range(1, 6))
            add(buf, lp(s * np.minimum(1, t / 0.05) * np.exp(-t * 1.2), 0.15) * 0.35, t0 + k * 0.34)
    elif name == 'rise':
        t = tt(d); f = 200 + 900 * (t / d) ** 2
        add(buf, np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / d) * 0.12 + lp(noise(d), 0.1) * (t / d) * 0.4, t0)
    elif name == 'steps':
        step = extra or 0.16; t = 0
        while t < d:
            add(buf, sfx_step(), t0 + t); t += step


def crowd(d, voices=90, claps=520):
    from scipy.signal import lfilter, fftconvolve
    n = int(d * SR); out = np.zeros(n)
    VOW = {'a': (800, 1200, 2500), 'e': (400, 2000, 2600), 'o': (500, 850, 2400), 'ay': (700, 1700, 2500)}
    def reson(x, f, bw):
        r = np.exp(-np.pi * bw / SR); th = 2 * np.pi * f / SR
        return lfilter([1 - r], [1, -2 * r * np.cos(th), r * r], x)
    for v in range(voices):
        kind = rng.choice(['m', 'm', 'f', 'k'])
        f0 = {'m': rng.uniform(140, 230), 'f': rng.uniform(260, 380), 'k': rng.uniform(380, 520)}[kind]
        st = rng.uniform(0, d * 0.55) if v > voices * 0.3 else rng.uniform(0, 0.4)
        L = min(d - st, rng.uniform(0.9, 2.8)); m = int(L * SR)
        if m < SR * 0.3: continue
        t = np.arange(m) / SR
        # نبرة «ييييه!»: صعود سريع ثم ثبات ثم هبوط، مع اهتزاز طبيعي
        glide = 1 + 0.35 * np.minimum(1, t / 0.18) - 0.25 * np.maximum(0, (t - L * 0.6) / (L * 0.4))
        f = f0 * glide * (1 + 0.012 * np.sin(2 * np.pi * rng.uniform(4.5, 6.5) * t) + 0.004 * rng.standard_normal(m).cumsum() / np.sqrt(np.arange(1, m + 1)))
        ph = np.cumsum(f) / SR
        src = 2 * (ph % 1) - 1                          # موجة منشارية (صوت الحنجرة)
        src += 0.04 * rng.uniform(-1, 1, m)             # نَفَس خفيف
        vw = VOW[rng.choice(list(VOW))]
        y = sum(reson(src, F * (1.12 if kind != 'm' else 1), 90 + 40 * k) * g for k, (F, g) in enumerate(zip(vw, (1, 0.6, 0.25))))
        e = np.minimum(1, t / 0.08) * np.minimum(1, (L - t) / 0.35) * (0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(1, 3) * t))
        i = int(st * SR); out[i:i + m] += y[:n - i] * e[:n - i] * rng.uniform(0.4, 1.0)
    out /= max(1e-6, np.abs(out).max())
    # تصفيق: مئات التصفيقات القصيرة بترددات مختلفة
    ap = np.zeros(n); cl = int(0.03 * SR)
    for k in range(claps):
        st = int(rng.uniform(0.15, d - 0.1) * SR)
        if st + cl >= n: continue
        burst = reson(rng.uniform(-1, 1, cl), rng.uniform(900, 2200), 700) * np.exp(-np.arange(cl) / SR * rng.uniform(90, 160))   # تصفيق بنطاق اليد لا هسهسة
        ap[st:st + cl] += burst * rng.uniform(0.3, 1)
    ap /= max(1e-6, np.abs(ap).max())
    mix = out * 0.9 + ap * 0.22
    tail = rng.standard_normal(int(1.1 * SR)) * np.exp(-np.arange(int(1.1 * SR)) / SR * 4.5)   # صدى ملعب
    wet = fftconvolve(mix, tail)[:n]; wet /= max(1e-6, np.abs(wet).max())
    res = mix * 0.7 + wet * 0.35
    t = np.arange(n) / SR
    res *= np.minimum(1, t / 0.2) * np.minimum(1, (d - t) / 1.5)
    return res / max(1e-6, np.abs(res).max()) * 0.75


def sfx_step():
    t = tt(0.08)
    return lp(noise(0.08), 0.3) * np.exp(-t * 50) * 0.7


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec'); ap.add_argument('-o', default='soundtrack.wav')
    a = ap.parse_args()
    S = json.load(open(a.spec, encoding='utf-8'))
    D = float(S['duration']); buf = np.zeros(int((D + 2) * SR)); mus = np.zeros_like(buf)
    for s in S.get('sections', []):
        section(mus, s, S.get('bpm', 110), S.get('key', 'C'))
    # تدرّج دخول وخروج المقاطع الموسيقية بنعومة
    buf += mus * S.get('music_gain', 0.8)
    for e in S.get('events', []):
        sfx(buf, e[0], e[1], e[2] if len(e) > 2 else 1.0, e[3] if len(e) > 3 else None)
    buf = buf[:int(D * SR)]
    fade = int(1.0 * SR); buf[-fade:] *= np.linspace(1, 0, fade)
    buf /= max(1e-6, np.abs(buf).max()) / 0.9
    w = wave.open(a.o, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((buf * 32767).astype(np.int16).tobytes()); w.close()
    print(f'  wrote {a.o} ({D:.1f}s)')


if __name__ == '__main__':
    main()
