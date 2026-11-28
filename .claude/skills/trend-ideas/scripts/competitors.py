#!/usr/bin/env python3
"""سحب آخر N مقطع لكل منافس من تيك توك وريلز إنستغرام عبر Apify، وتحليلهم في تقرير.

  competitors.py --handles "m.jabaly,krwanbasha" [--ig "m.jabaly,..."] --n 30 --budget 1.5 -o reports/competitors

- --handles: حسابات تيك توك. --ig: حسابات إنستغرام (افتراضياً نفس الأسماء).
- التكلفة: تيك توك 0.0037$/مقطع، إنستغرام 0.0026$/ريل، + 0.001$ لكل تشغيل. يرفض إن تجاوز --budget.
- الناتج: competitors-YYYY-MM-DD.md (تقرير) و.json (كل المقاطع) في مجلد الإخراج.
"""
import argparse, collections, datetime as dt, json, os, re, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trends

IG_PRICE = 0.0026


def norm_ig(it):
    views = it.get('videoPlayCount') or it.get('videoViewCount') or 0
    eng = (it.get('likesCount') or 0) + (it.get('commentsCount') or 0)
    return {'platform': 'Instagram', 'title': (it.get('caption') or '').strip(), 'url': it.get('url'),
            'views': views, 'likes': it.get('likesCount') or 0, 'comments': it.get('commentsCount') or 0, 'shares': 0,
            'eng': eng, 'author': it.get('ownerUsername'), 'followers': None, 'date': it.get('timestamp'),
            'duration': round(it.get('videoDuration') or 0), 'tags': it.get('hashtags') or []}


def summarize(vs):
    if not vs:
        return None
    views = [v['views'] for v in vs]
    dates = sorted(trends.days_since(v['date']) or 0 for v in vs)
    span = max(dates) - min(dates) if len(dates) > 1 else 0
    durs = [float(v['duration']) for v in vs if str(v['duration'] or '').replace('.', '').isdigit() and float(v['duration']) > 0]
    hooks = [re.split(r'[\n.!؟?]', v['title'])[0][:60] for v in sorted(vs, key=lambda x: -x['views'])[:5]]
    return {'n': len(vs), 'avg': int(st.mean(views)), 'med': int(st.median(views)), 'max': max(views),
            'er': round(100 * sum(v['eng'] for v in vs) / max(1, sum(views)), 1),
            'per_week': round(len(vs) / max(1, span / 7), 1) if span else None,
            'dur': round(st.median(durs)) if durs else None, 'hooks': hooks,
            'top': sorted(vs, key=lambda x: -x['views'])[:3],
            'tags': collections.Counter(t.lower() for v in vs for t in v['tags']).most_common(8)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--handles', required=True)
    ap.add_argument('--ig', default=None)
    ap.add_argument('--n', type=int, default=30)
    ap.add_argument('--budget', type=float, default=1.5)
    ap.add_argument('-o', default='reports/competitors')
    ap.add_argument('--from-json', help='إعادة بناء التقرير من JSON محفوظ بلا سحب (بلا تكلفة)')
    a = ap.parse_args()
    tt = [h.strip().lstrip('@') for h in a.handles.split(',') if h.strip()]
    ig = [h.strip().lstrip('@') for h in (a.ig or a.handles).split(',') if h.strip()]
    est = len(tt) * a.n * trends.PRICE['tiktok'] + len(ig) * a.n * IG_PRICE + 0.002
    if a.from_json:
        vids = json.load(open(a.from_json, encoding='utf-8')); est = 0
        return write_report(vids, tt, ig, a, est)
    print(f'  التكلفة التقديرية: ~{est:.2f}$ (الحد {a.budget}$)', file=sys.stderr)
    if est > a.budget:
        sys.exit('  ✗ التقدير يتجاوز الحد.')
    vids = []
    items = trends.run_actor('clockworks/tiktok-scraper', {'profiles': tt, 'resultsPerPage': a.n, 'profileScrapeSections': ['videos'],
                             'profileSorting': 'latest', 'excludePinnedPosts': True, 'shouldDownloadVideos': False,
                             'shouldDownloadCovers': False, 'shouldDownloadAvatars': False})
    vids += [trends.score(trends.norm_tiktok(i)) for i in items if i.get('playCount') is not None]
    print(f'  تيك توك: {len(items)}', file=sys.stderr)
    items = trends.run_actor('apify/instagram-reel-scraper', {'username': ig, 'resultsLimit': a.n, 'skipPinnedPosts': True})
    vids += [trends.score(norm_ig(i)) for i in items if i.get('ownerUsername')]
    print(f'  إنستغرام: {len(items)}', file=sys.stderr)

    os.makedirs(a.o, exist_ok=True)
    json.dump(vids, open(os.path.join(a.o, f'competitors-{dt.date.today().isoformat()}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    write_report(vids, tt, ig, a, est)


def write_report(vids, tt, ig, a, est):
    fans = {v['author']: v['followers'] for v in vids if v['platform'] == 'TikTok' and v['followers']}
    os.makedirs(a.o, exist_ok=True)
    stamp = dt.date.today().isoformat()
    F = trends.fmt
    L = [f'# تحليل المنافسين — {stamp}', '', f'آخر {a.n} مقطعاً لكل حساب من تيك توك وريلز إنستغرام. التكلفة التقديرية ~{est:.2f}$.', '',
         '## الملخص', '', '| الحساب | المنصة | المتابعون | المقاطع | متوسط المشاهدات | الوسيط | الأعلى | التفاعل | نشر/أسبوع | المدة (ث) |',
         '|---|---|---|---|---|---|---|---|---|---|']
    S = {}
    for h in tt:
        for plat, name in (('TikTok', h), ('Instagram', ig[tt.index(h)] if tt.index(h) < len(ig) else h)):
            s = summarize([v for v in vids if v['platform'] == plat and (v['author'] or '').lower() == name.lower()])
            S[(h, plat)] = s
            if s:
                L.append(f"| {h} | {plat} | {F(fans.get(h)) if plat == 'TikTok' and fans.get(h) else '—'} | {s['n']} | {F(s['avg'])} | {F(s['med'])} | {F(s['max'])} | {s['er']}% | {s['per_week'] or '—'} | {s['dur'] or '—'} |")
            else:
                L.append(f'| {h} | {plat} | — | 0 | لم يُعثر على الحساب بهذا الاسم | | | | | |')
    # ---- المشاهدات العالية: الأعلى عموماً، والأعلى يومياً، والمقاطع الفيروسية الشاذة (≥3× وسيط صاحبها)
    med = {}
    for v in vids:
        med.setdefault((v['author'], v['platform']), []).append(v['views'])
    med = {k: st.median(x) for k, x in med.items()}
    row = lambda k, v, extra='': f"| {k} | {v['author']} | {v['platform']} | {F(v['views'])} | {F(v['vpd'])} | {v['er']}% | {v['duration'] or ''} |{extra} {re.sub(r'\s+', ' ', v['title'])[:70].replace('|', '/')} | [رابط]({v['url']}) |"
    L += ['', '## 🔥 أعلى المقاطع مشاهدة (كل المنافسين، المنصتين)', '',
          '| # | الحساب | المنصة | المشاهدات | يومياً | التفاعل | المدة | الافتتاحية | الرابط |', '|---|---|---|---|---|---|---|---|---|']
    L += [row(k, v) for k, v in enumerate(sorted(vids, key=lambda v: -v['views'])[:15], 1)]
    L += ['', '## ⚡ الأسرع انتشاراً الآن (مشاهدات يومية)', '',
          '| # | الحساب | المنصة | المشاهدات | يومياً | التفاعل | المدة | الافتتاحية | الرابط |', '|---|---|---|---|---|---|---|---|---|']
    L += [row(k, v) for k, v in enumerate(sorted(vids, key=lambda v: -v['vpd'])[:10], 1)]
    out = [(v['views'] / max(1, med[(v['author'], v['platform'])]), v) for v in vids if med.get((v['author'], v['platform']))]
    out = sorted([o for o in out if o[0] >= 3], key=lambda o: -o[0])
    L += ['', '## 🚀 المقاطع الفيروسية الشاذة (≥ 3 أضعاف المعتاد عند صاحبها)', '',
          'هذه الأهم: نجحت **الفكرة نفسها** لا شهرة الحساب. انسخ النمط لا المحتوى.', '',
          '| # | الحساب | المنصة | المشاهدات | يومياً | التفاعل | المدة | × المعتاد | الافتتاحية | الرابط |', '|---|---|---|---|---|---|---|---|---|---|']
    L += [row(k, v, f' {r:.1f}× |') for k, (r, v) in enumerate(out[:20], 1)]
    L += ['', '## تفاصيل كل منافس', '']
    for h in tt:
        L.append(f'### {h}')
        for plat in ('TikTok', 'Instagram'):
            s = S.get((h, plat))
            if not s:
                continue
            L.append(f'**{plat}** — أقوى 3 مقاطع:')
            for v in s['top']:
                t = re.sub(r'\s+', ' ', v['title'])[:90].replace('|', '/')
                L.append(f"- {F(v['views'])} مشاهدة، تفاعل {v['er']}% — {t} [رابط]({v['url']})")
            L.append('- افتتاحيات أقوى مقاطعه: ' + ' / '.join(f'«{x}»' for x in s['hooks'] if x))
            L.append('- هاشتاغات متكررة: ' + '، '.join(f'#{t}' for t, _ in s['tags']))
            L.append('')
    open(os.path.join(a.o, f'competitors-{stamp}.md'), 'w', encoding='utf-8').write('\n'.join(L))
    print(os.path.join(a.o, f'competitors-{stamp}.md'))
    return L


if __name__ == '__main__':
    main()
