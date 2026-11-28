#!/usr/bin/env python3
"""بانِي مقاطع «الشرح بالبطاقات» (engine/explainer.html) — نظام تصميم خاص لكل مقطع.

  explainer.py episode.json -o timeline.json            (يبني الخط الزمني؛ مع voice يزامن، وبدونه يقدّر الإيقاع)
  explainer.py episode.json --voice-text voice.txt      (يكتب نص التعليق الصوتي كاملاً لتوليد الصوت)

episode.json:
{ "style": {bg1,bg2,blob1..3,ink,muted,accent,good,bad,card,capbg,capink,font,...},   ← هوية هذا المقطع فقط
  "handle": "@...", "voice": "voice.mp3", "music": "playful", "music_volume": 0.2, "pace": 2.3,
  "scenes": [ { "say": "نص يُقال مع *كلمة* مميزة", "head": {"pre":"..","main":"..","key":".."}, "badge": "..",
                "cards": [ {"t":"img","src":"img/a.png","tag":{"text":"✕ لا","kind":"bad"}},
                           {"t":"label","title":"..","rows":[{"k":"..","v":"..","hi":true}]},
                           {"t":"spoons","n":9,"unit":"ملاعق","w":"ملاعق"},      ← w: كلمة تبدأ عندها الحركة
                           {"t":"bars","max":40,"limit":25,"items":[{"label":"..","value":35,"text":"35غ","over":true}]},
                           {"t":"myth","text":"..","w":"خرافة"}, {"t":"check","items":[{"text":"..","w":"فاكهة"}]},
                           {"t":"comment","text":"صحة"} ] } ] }
"""
import argparse, json, os, re, subprocess, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import salam

PUNCT = '.،,؛;:!؟?…'


def words_of(say):
    out = []
    for raw in say.split():
        key = raw.startswith('*') or raw.rstrip(PUNCT).endswith('*')
        w = raw.replace('*', '')
        out.append({'w': w, 'say': w, 'key': key, 'spoken': True, 'shown': True})
    return out


def find(ws, needle, after=0.0):
    n = salam.norm(needle)
    for x in ws:
        if salam.norm(x['w']).startswith(n) and x['t'] >= after - 1e-6:
            return x['t']
    return None


def build(spec, base, out):
    scenes = spec['scenes']
    W = [words_of(s['say']) for s in scenes]
    flat = [x for ws in W for x in ws]
    voice = spec.get('voice')
    vpath = os.path.join(base, voice) if voice else None
    if vpath and os.path.exists(vpath):
        tmp = tempfile.mkdtemp(); wav = os.path.join(tmp, 'v.wav'); salam.to_wav(vpath, wav)
        dur = salam.duration(vpath)
        words = json.load(open(os.path.join(base, spec['words']), encoding='utf-8')) if spec.get('words') else salam.whisper_words(wav)
        method = salam.align_tokens(flat, words, wav); shutil.rmtree(tmp, ignore_errors=True)
    else:   # بلا صوت بعد: تقدير بإيقاع الإلقاء
        pace, t = float(spec.get('pace', 2.3)), 0.4
        avg = sum(salam.nchars(x['w']) for x in flat) / len(flat)
        for ws in W:
            for x in ws:
                x['t'] = round(t, 3); t += (0.55 + 0.45 * salam.nchars(x['w']) / avg) / pace
                if x['w'][-1:] in '.؟?!': t += 0.18
            t += 0.3
        dur, method = t + 1.0, f'pace {pace}'
    S = []
    for i, (s, ws) in enumerate(zip(scenes, W)):
        st = 0.0 if i == 0 else round(ws[0]['t'] - 0.15, 3)
        S.append({'start': st, '_ws': ws, 'src': s})
    for i, sc in enumerate(S):
        sc['end'] = S[i + 1]['start'] if i + 1 < len(S) else round(dur, 3)
    TL = {'engine': 'explainer.html', 'width': 1080, 'height': 1920, 'fps': 30, 'duration': round(dur, 3),
          'style': spec.get('style', {}), 'handle': spec.get('handle', ''), 'align': method, 'scenes': []}
    if vpath and os.path.exists(vpath):
        TL['audio'] = os.path.relpath(vpath, os.path.dirname(os.path.abspath(out)))
    for k in ('music', 'music_volume', 'voice_volume'):
        if k in spec:
            TL[k] = spec[k] if k != 'music' or spec[k] in ('auto', 'calm', 'playful') else os.path.relpath(os.path.join(base, spec[k]), os.path.dirname(os.path.abspath(out)))
    TL['sfx'] = spec.get('sfx', False)
    for sc in S:
        s, ws = sc['src'], sc['_ws']
        o = {'start': sc['start'], 'end': sc['end']}
        for k in ('head', 'badge', 'video_from', 'video_rate', 'zoom'):
            if k in s:
                o[k] = s[k]
        if s.get('video'):
            o['video'] = os.path.relpath(os.path.join(base, s['video']), os.path.dirname(os.path.abspath(out)))
        cards = []
        for c in s.get('cards', []):
            c = dict(c)
            if 'src' in c:
                c['src'] = os.path.relpath(os.path.join(base, c['src']), os.path.dirname(os.path.abspath(out)))
            if c.get('w'):   # ربط الحركة بلحظة نطق كلمة
                tw = find(ws, c['w'], sc['start'])
                if tw is not None:
                    c.update({'from': tw, 'to': min(sc['end'] - 0.5, tw + c.get('span', 2.2)), 'at': tw, 'stampAt': tw})
            if c['t'] == 'check':
                c['times'] = [find(ws, it.get('w', it['text'].split()[0]), sc['start']) for it in c['items']]
            if c.get('at_rel') is not None:
                c['at'] = sc['start'] + c['at_rel']
            cards.append(c)
        o['cards'] = cards
        # الترجمة: مقاطع ≤4 كلمات، تنكسر عند علامات الوقف
        caps, cur = [], []
        for x in ws:
            cur.append(x)
            if len(cur) >= 4 or x['w'][-1:] in PUNCT:
                caps.append(cur); cur = []
        if cur:
            caps.append(cur)
        o['caps'] = []
        for j, ch in enumerate(caps):
            a = ch[0]['t'] - 0.05
            b = caps[j + 1][0]['t'] - 0.05 if j + 1 < len(caps) else sc['end'] - 0.05
            o['caps'].append({'start': round(a, 3), 'end': round(b, 3),
                              'words': [{'w': x['w'].strip(PUNCT) if x['w'][-1:] in '.،,' else x['w'], **({'key': True} if x['key'] else {})} for x in ch]})
        TL['scenes'].append(o)
    return TL


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('spec')
    ap.add_argument('-o', default='timeline.json')
    ap.add_argument('--voice-text')
    a = ap.parse_args()
    spec = json.load(open(a.spec, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(a.spec))
    if a.voice_text:
        txt = '\n'.join(s['say'].replace('*', '') for s in spec['scenes'])
        open(a.voice_text, 'w', encoding='utf-8').write(txt + '\n'); print(a.voice_text); return
    tl = build(spec, base, a.o)
    json.dump(tl, open(a.o, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"  wrote {a.o} ({len(tl['scenes'])} scenes, align={tl['align']}, {tl['duration']}s)")


if __name__ == '__main__':
    main()
