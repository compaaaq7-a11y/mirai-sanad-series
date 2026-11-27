#!/usr/bin/env python3
"""salam-skill — من ستوري بورد نصي إلى فيديو مونتاج "ضربة" متزامن مع الصوت.

الأوامر:
  salam.py tts      board.txt -o voice.mp3 [--voice ar-SA-HamedNeural] [--rate +12%]
  salam.py timeline board.txt voice.mp3 -o timeline.json [--words words.json]
  salam.py timeline board.txt -o timeline.json [--pace 2.3]    (بدون صوت: توقيت بإيقاع الإلقاء)
  salam.py render   timeline.json -o out.mp4 [--scale 0.5] [--still 1,5,9]
  salam.py make     board.txt voice.mp3 -o out.mp4 [--scale 0.5]   (timeline + render)

صيغة الستوري بورد (سطر = مشهد = قطع):
  [bg=dark fx=ring,sparks] ضربة وحدة
  [bg=red] *تكفي*
  [bg=camera] قدامك / +*الحين؟*
  *كلمة*  = لون التمييز (أحمر، أو أسود على الخلفية الحمراء)
  +كلمة   = أكبر 35%     -كلمة = أصغر 30%
  /       = سطر جديد داخل نفس المشهد
  {نص}    = يُنطق ولا يُكتب على الشاشة      <نص> = يُكتب ولا يُنطق
  [bg=image prompt="old father drinking coffee"] خلفية صورة مولّدة مجاناً (أو image=ملف.jpg)
  الأسطر التي تبدأ بـ # تعليقات. وتُضبط الإعدادات العامة بسطر مثل:  @ music=bgm.mp3 music_volume=0.1
"""
import argparse, json, os, re, shlex, subprocess, sys, wave, shutil, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(HERE, '..', 'engine')

DEFAULT_COLOR = {'dark': 'white', 'red': 'silver', 'cream': 'black', 'camera': 'black', 'image': 'white', 'video': 'white'}
ACCENT_COLOR = {'dark': 'red', 'red': 'black', 'cream': 'red', 'camera': 'red', 'image': 'red', 'video': 'red'}
BG_CYCLE = ['dark', 'red', 'cream', 'dark', 'red', 'camera']
STRIP_DISPLAY = '.،,؛;:!…'


# ---------------------------------------------------------------- parsing
def parse_board(path):
    scenes, glob = [], {}
    for raw in open(path, encoding='utf-8'):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('@'):
            glob.update(parse_kv(line[1:]))
            continue
        attrs = {}
        m = re.match(r'^\[(.*?)\]\s*(.*)$', line)
        if m:
            attrs, line = parse_kv(m.group(1)), m.group(2)
        scenes.append({'attrs': attrs, 'text': line})
    for i, s in enumerate(scenes):
        s['attrs'].setdefault('bg', BG_CYCLE[i % len(BG_CYCLE)])
        a = s['attrs']
        # صورة بصبغة حمراء تُعامل ألوانها مثل الخلفية الحمراء (تمييز أسود)
        s['tokens'] = tokenize(s['text'], 'red' if a['bg'] == 'image' and a.get('tint') == 'red' else a['bg'])
    return scenes, glob


def parse_kv(s):
    out = {}
    for tok in shlex.split(s):
        if '=' in tok:
            k, v = tok.split('=', 1)
            out[k.strip()] = v
    return out


def tokenize(text, bg):
    """يُرجع قائمة عناصر: {'w','spoken','shown','c','s','newline'}"""
    toks, open_star = [], [False]
    # نص منطوق فقط {...} ونص مكتوب فقط <...>
    parts = re.split(r'(\{[^}]*\}|<[^>]*>)', text)
    for pi, part in enumerate(parts):
        if not part:
            continue
        spoken_only = part.startswith('{')
        shown_only = part.startswith('<')
        body = part[1:-1] if (spoken_only or shown_only) else part
        for raw in body.split():
            if raw == '/':
                toks.append({'newline': True})
                continue
            w, size, accent = raw, 1.0, False
            while w[:1] in '+-':
                size *= 1.35 if w[0] == '+' else 0.7
                w = w[1:]
            # تمييز يمتد على عدة كلمات: *كلمة كلمة*
            if w.startswith('*'):
                accent, w = True, w[1:]
                if not w.endswith('*'):
                    open_star[0] = True
            elif open_star[0]:
                accent = True
            if w.endswith('*'):
                accent, w, open_star[0] = True, w[:-1], False
            if not w:
                continue
            shown = w.strip(STRIP_DISPLAY)
            toks.append({'w': shown, 'say': w, 'spoken': not shown_only, 'part': pi, 'spoken_only': spoken_only, 'shown': not spoken_only and bool(shown),
                         'c': ACCENT_COLOR[bg] if accent else DEFAULT_COLOR[bg], 's': round(size, 3)})
    return toks


def spoken_text(scenes):
    out = []
    for s in scenes:
        words = [t['say'] for t in s['tokens'] if not t.get('newline') and t['spoken']]
        if words:
            out.append(' '.join(words))
    return '\n'.join(out)


LETTERS = re.compile(r'[\w؀-ۿ]')


def nchars(w):
    return max(1, len(LETTERS.findall(w)))


# ---------------------------------------------------------------- audio
def to_wav(src, dst):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ac', '1', '-ar', '16000', dst], check=True)


def duration(src):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def whisper_words(wav):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    try:
        model = WhisperModel(os.environ.get('SALAM_WHISPER', 'small'), device='cpu', compute_type='int8')
        segs, _ = model.transcribe(wav, language='ar', word_timestamps=True, vad_filter=False)
        words = [{'w': w.word.strip(), 'start': w.start, 'end': w.end} for s in segs for w in s.words]
        return words or None
    except Exception as e:  # شبكة محجوبة أو نموذج غير متاح
        print('  whisper unavailable:', e.__class__.__name__, file=sys.stderr)
        return None


def speech_intervals(wav):
    """كشف مقاطع الكلام بالطاقة (بديل عند غياب whisper)."""
    import numpy as np
    w = wave.open(wav)
    sr = w.getframerate()
    x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    hop = int(sr * 0.02)
    rms = np.array([np.sqrt((x[i:i + hop] ** 2).mean() + 1e-12) for i in range(0, len(x) - hop, hop)])
    db = 20 * np.log10(rms)
    thr = max(db.max() - 32, np.percentile(db, 20) + 6)
    on = db > thr
    # إغلاق الفجوات القصيرة (<120ms) وحذف الومضات (<60ms)
    iv, start = [], None
    for i, v in enumerate(list(on) + [False]):
        if v and start is None:
            start = i
        if not v and start is not None:
            iv.append([start * 0.02, i * 0.02])
            start = None
    merged = []
    for a, b in iv:
        if merged and a - merged[-1][1] < 0.12:
            merged[-1][1] = b
        else:
            merged.append([a, b])
    return [m for m in merged if m[1] - m[0] >= 0.06]


def time_of_fraction(anchors, f):
    """anchors: قائمة (fraction, time) مرتبة. استيفاء خطي."""
    if f <= anchors[0][0]:
        return anchors[0][1]
    for (f0, t0), (f1, t1) in zip(anchors, anchors[1:]):
        if f <= f1:
            return t0 + (t1 - t0) * (f - f0) / max(1e-9, f1 - f0)
    return anchors[-1][1]


NORM = str.maketrans({'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ة': 'ه', 'ى': 'ي', 'ؤ': 'و', 'ئ': 'ي'})


def norm(w):
    w = re.sub(r'[\u064B-\u0652\u0640«»"\'.,،؟?!:;…]', '', w).translate(NORM)
    return w.lower()


def split_words(words):
    """يفكّ المدخلات متعددة الكلمات إلى كلمات مفردة مع توقيت مستوفى بعدد الحروف."""
    out = []
    for e in words:
        parts = e['w'].split() or [e['w']]
        total = sum(nchars(p) for p in parts)
        acc = 0
        for p in parts:
            out.append({'w': p, 't': e['start'] + (e['end'] - e['start']) * acc / total})
            acc += nchars(p)
    return out


def align_tokens(spoken, words, wav):
    """يعطي كل كلمة منطوقة في الستوري بورد توقيتها t.
    مع نص مفرّغ (whisper أو words.json): مطابقة كلمة بكلمة ثم استيفاء للكلمات غير المطابقة.
    بدونه: توزيع الحروف على مقاطع الكلام المكتشفة بالطاقة."""
    if words:
        import difflib
        ref = split_words(words)
        a = [norm(t['say']) for t in spoken]
        b = [norm(w['w']) for w in ref]
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                spoken[blk.a + k]['t'] = ref[blk.b + k]['t']
        # استيفاء غير المطابق بين أقرب جارين مطابقين
        known = [i for i, t in enumerate(spoken) if 't' in t]
        if not known:
            return align_tokens(spoken, None, wav)
        end_t = words[-1]['end']
        for i, t in enumerate(spoken):
            if 't' in t:
                continue
            prev = max([k for k in known if k < i], default=None)
            nxt = min([k for k in known if k > i], default=None)
            t0 = spoken[prev]['t'] if prev is not None else ref[0]['t']
            t1 = spoken[nxt]['t'] if nxt is not None else end_t
            lo = prev if prev is not None else -1
            hi = nxt if nxt is not None else len(spoken)
            t['_t'] = t0 + (t1 - t0) * (i - lo) / (hi - lo)
        for t in spoken:
            if '_t' in t:
                t['t'] = t.pop('_t')
            t['t'] = round(t['t'], 3)
        return 'transcript'
    iv = speech_intervals(wav)
    total_time = sum(b - a for a, b in iv)
    anchors, acc = [], 0
    for a, b in iv:
        anchors.append((acc / total_time, a))
        acc += b - a
        anchors.append((acc / total_time, b))
    total = sum(nchars(t['say']) for t in spoken)
    acc = 0
    for t in spoken:
        t['t'] = round(time_of_fraction(anchors, acc / total), 3)
        acc += nchars(t['say'])
    return 'energy'


# ---------------------------------------------------------------- timeline
def pace_times(scenes, wps):
    """بدون صوت: توقيت بإيقاع الإلقاء المرجعي (كلمات/ثانية) مع نَفَس قصير عند كل قطع."""
    t, avg = (0.0 if all('dur' in s['attrs'] for s in scenes) else 0.35), None
    toks = [x for s in scenes for x in s['tokens'] if not x.get('newline') and x['spoken']]
    avg = sum(nchars(x['say']) for x in toks) / max(1, len(toks))
    for s in scenes:
        words = [x for x in s['tokens'] if not x.get('newline') and x['spoken']]
        if 'dur' in s['attrs']:
            # مشهد بمدة محددة: الكلمات تتوزع داخلها (بداية بعد 0.4ث، ونهاية قبل آخر 0.8ث)
            d = float(s['attrs']['dur'])
            s['_start'] = t
            span = max(0.3, d - 1.2)
            w8 = [0.55 + 0.45 * nchars(x['say']) / avg for x in words]
            acc = 0
            for x, w in zip(words, w8):
                x['t'] = round(t + 0.4 + span * acc / max(1e-9, sum(w8)), 3)
                acc += w
            t += d
            continue
        for x in words:
            x['t'] = round(t, 3)
            t += (0.55 + 0.45 * nchars(x['say']) / avg) / wps
            if x['say'][-1:] in '.؟?!':
                t += 0.12
        t += 0.12
    if all('dur' in s['attrs'] for s in scenes):
        return t
    return t + 0.9


def make_timeline(board, audio, words_path=None, out=None, pace=2.3):
    scenes, glob = parse_board(board)
    spoken = [t for s in scenes for t in s['tokens'] if not t.get('newline') and t['spoken']]
    if audio:
        tmp = tempfile.mkdtemp()
        wav = os.path.join(tmp, 'v.wav')
        to_wav(audio, wav)
        dur = duration(audio)
        words = json.load(open(words_path, encoding='utf-8')) if words_path else whisper_words(wav)
        method = align_tokens(spoken, words, wav)
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        pace = float(glob.get('pace', pace))
        dur, method = pace_times(scenes, pace), f'pace {pace} w/s (no audio)'

    out_scenes = []
    for i, s in enumerate(scenes):
        a = s['attrs']
        toks = s['tokens']
        times = [t['t'] for t in toks if 't' in t]
        first = min(times) if times else (out_scenes[-1]['_last'] + 0.3 if out_scenes else 0)
        lines, cur = [], []
        last_t = first
        for t in toks:
            if t.get('newline'):
                if cur:
                    lines.append(cur)
                cur = []
                continue
            if 't' in t:
                last_t = t['t']
            if t['shown'] and 't' not in t:
                # كلمة تُكتب ولا تُنطق: تظهر مع بداية الجزء المنطوق {..} الذي قبلها مباشرة
                grp = [x['t'] for x in toks if x.get('part') == t['part'] - 1 and x.get('spoken_only') and 't' in x]
                t['t'] = min(grp) if grp else last_t
            if t['shown']:
                cur.append({'w': t['w'], 't': t['t'], 'c': t['c'], **({'s': t['s']} if t['s'] != 1 else {})})
        if cur:
            lines.append(cur)
        sc = {'start': round(s['_start'], 3) if '_start' in s else round(max(0.0, first - 0.08), 3), 'bg': a['bg'], 'lines': lines, '_last': last_t}
        if a['bg'] == 'image':
            sc['image'] = resolve_image(a, glob, board, out, i)
            if a.get('tint'):
                sc['tint'] = a['tint']
        if a.get('fx'):
            sc['fx'] = [f for f in a['fx'].split(',') if f]
        for k in ('y', 'size', 'push', 'tilt'):
            if k in a:
                sc[k] = float(a[k])
        if a.get('cut') in ('soft', 'fade'):
            sc['soft'] = True
        if a.get('cut') == 'fade' or 'xfade' in a:
            sc['xfade'] = float(a.get('xfade', 0.6))
        if a['bg'] == 'video':
            sc['video'] = os.path.relpath(os.path.join(os.path.dirname(os.path.abspath(board)), a['video']),
                                          os.path.dirname(os.path.abspath(out or board)))
            for k in ('video_from', 'video_rate', 'video_volume'):
                if k in a:
                    sc[k] = float(a[k])
            if a.get('video_loop') == 'no':
                sc['video_loop'] = False
        if 'bubble' in a:
            sc['bubble'] = a['bubble']
            for k in ('bubble_x', 'bubble_y', 'bubble_rot'):
                if k in a:
                    sc[k] = float(a[k])
            if 'bubble_at' in a:
                sc['bubble_t'] = sc['start'] + float(a['bubble_at'])
        for k in ('move', 'focus', 'fade', 'font'):
            if k in a:
                sc[k] = a[k]
        if a.get('enter') == 'gentle' or glob.get('enter') == 'gentle':
            sc['gentle'] = True
        if a.get('reflect') == 'no':
            sc['reflect'] = False
        if a.get('prop'):
            sc['prop'] = make_prop(a)
        out_scenes.append(sc)
    out_scenes[0]['start'] = 0.0
    for i, sc in enumerate(out_scenes):
        sc['end'] = out_scenes[i + 1]['start'] if i + 1 < len(out_scenes) else round(dur, 3)
        sc.pop('_last')
        # الطباعة في الشات والتعليقات تتبع توقيت المشهد
        p = sc.get('prop')
        if p and p['type'] == 'chat' and 'type_from' not in p:
            p['type_from'], p['type_to'] = sc['start'] + 0.25, max(sc['start'] + 0.6, sc['end'] - 0.25)
    # نفس الصورة عبر قطع ناعم: حركة الكاميرا تستمر بلا قفزة
    g = 0
    while g < len(out_scenes):
        h = g
        while (h + 1 < len(out_scenes) and out_scenes[h + 1].get('image') and out_scenes[h + 1].get('image') == out_scenes[g].get('image')
               and out_scenes[h + 1].get('soft') and not out_scenes[h + 1].get('xfade')):
            h += 1
        if h > g:
            for k in range(g, h + 1):
                out_scenes[k]['kb_start'], out_scenes[k]['kb_end'] = out_scenes[g]['start'], out_scenes[h]['end']
                if 'move' in out_scenes[g]:
                    out_scenes[k].setdefault('move', out_scenes[g]['move'])
        g = h + 1
    tl = {'width': 1080, 'height': 1920, 'fps': int(glob.get('fps', 30)), 'duration': round(dur, 3),
          'audio': os.path.relpath(os.path.abspath(audio), os.path.dirname(os.path.abspath(out or 'x'))) if audio else None,
          'align': method, 'scenes': out_scenes}
    if 'font' in glob:
        tl['font'] = glob['font']
    for k in ('size', 'bubble_scale'):   # حجم النص الأساسي (الافتراضي 165) وحجم فقاعات الكوميكس للفيديو كله
        if k in glob:
            tl[k] = float(glob[k])
    for k in ('music', 'music_volume', 'voice_volume', 'whoosh_volume', 'hit_volume', 'sfx'):
        if k in glob:
            v = glob[k]
            tl[k] = (v != 'no') if k == 'sfx' else (float(v) if k.endswith('volume') else v if v in ('auto', 'calm') else
                                                     os.path.relpath(os.path.abspath(v), os.path.dirname(os.path.abspath(out or 'x'))))
    return tl


def resolve_image(a, glob, board, out, i):
    """خلفية صورة: image=ملف موجود، أو prompt=وصف يُولَّد مجاناً (Pollinations) ويُحفظ في images/ بجانب الستوري بورد."""
    out_dir = os.path.dirname(os.path.abspath(out or board))
    if a.get('image'):
        src = os.path.join(os.path.dirname(os.path.abspath(board)), a['image'])
    else:
        prompt = a.get('prompt')
        if not prompt:
            raise SystemExit(f'scene {i + 1}: bg=image needs image=path or prompt="..."')
        style = glob.get('image_style', 'cinematic, dramatic warm light, shallow depth of field, photorealistic, vertical 9:16, no text')
        full = f'{prompt}, {style}'
        sys.path.insert(0, HERE)
        import imagegen
        img_dir = os.path.join(os.path.dirname(os.path.abspath(board)), 'images')
        os.makedirs(img_dir, exist_ok=True)
        seed = int(a.get('seed', glob.get('seed', 7)))
        src = os.path.join(img_dir, imagegen.cache_name(full, 1080, 1920, seed, glob.get('image_model')))
        if not os.path.exists(src):
            print(f'  generating image for scene {i + 1}: {prompt[:60]}', file=sys.stderr)
        imagegen.generate(full, src, 1080, 1920, seed, glob.get('image_model'))
    return os.path.relpath(src, out_dir)


def make_prop(a):
    t = a['prop']
    p = {'type': t}
    if t == 'chat':
        for k in ('question', 'text', 'file', 'reply', 'model', 'header'):
            if k in a:
                p[k] = a[k]
    elif t == 'phone':
        for k in ('app', 'hero', 'title', 'desc', 'button', 'comment', 'tabs'):
            if k in a:
                p[k] = a[k]
        if any(k.startswith('dm_') for k in a):
            p['dm'] = {k[3:]: v for k, v in a.items() if k.startswith('dm_')}
    elif t == 'cards':
        p['items'] = a.get('items', '').split('|')
    if 'prop_y' in a:
        p['y'] = float(a['prop_y'])
    return p


# ---------------------------------------------------------------- tts
def tts(board, out, voice, rate, pitch):
    scenes, _ = parse_board(board)
    text = spoken_text(scenes)
    try:
        import edge_tts  # noqa: F401
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'edge-tts'], check=True)
    subprocess.run(['edge-tts', '--voice', voice, f'--rate={rate}', f'--pitch={pitch}', '--text', text,
                    '--write-media', out], check=True)
    print('  wrote', out)


def render(tl_path, out, extra):
    node_path = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip()
    env = dict(os.environ, NODE_PATH=os.pathsep.join(filter(None, [os.environ.get('NODE_PATH'), node_path])))
    subprocess.run(['node', os.path.join(ENGINE, 'render.mjs'), tl_path, out, *extra], check=True, env=env)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('tts'); a.add_argument('board'); a.add_argument('-o', required=True)
    a.add_argument('--voice', default='ar-SA-HamedNeural'); a.add_argument('--rate', default='+12%'); a.add_argument('--pitch', default='+0Hz')
    b = sub.add_parser('timeline'); b.add_argument('board'); b.add_argument('audio', nargs='?'); b.add_argument('-o', required=True); b.add_argument('--words'); b.add_argument('--pace', type=float, default=2.3)
    c = sub.add_parser('render'); c.add_argument('timeline'); c.add_argument('-o', required=True)
    d = sub.add_parser('make'); d.add_argument('board'); d.add_argument('audio', nargs='?'); d.add_argument('-o', required=True); d.add_argument('--words'); d.add_argument('--pace', type=float, default=2.3)
    for p in (c, d):
        p.add_argument('--scale'); p.add_argument('--still'); p.add_argument('--no-sfx', action='store_true')
    args = ap.parse_args()

    def extra():
        e = []
        if args.scale: e += ['--scale', args.scale]
        if args.still: e += ['--still', args.still]
        if args.no_sfx: e += ['--no-sfx']
        return e

    if args.cmd == 'tts':
        tts(args.board, args.o, args.voice, args.rate, args.pitch)
    elif args.cmd == 'timeline':
        tl = make_timeline(args.board, args.audio, args.words, args.o, args.pace)
        json.dump(tl, open(args.o, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"  wrote {args.o}  ({len(tl['scenes'])} scenes, align={tl['align']}, {tl['duration']}s)")
    elif args.cmd == 'render':
        render(args.timeline, args.o, extra())
    elif args.cmd == 'make':
        tl_path = os.path.splitext(args.o)[0] + '.timeline.json'
        tl = make_timeline(args.board, args.audio, args.words, tl_path, args.pace)
        json.dump(tl, open(tl_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f"  timeline: {tl_path}  ({len(tl['scenes'])} scenes, align={tl['align']})")
        render(tl_path, args.o, extra())


if __name__ == '__main__':
    main()
