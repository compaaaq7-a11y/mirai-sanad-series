#!/usr/bin/env python3
"""جمع المقاطع الرائجة من تيك توك ويوتيوب عبر Apify، وترتيبها، وكتابة تقرير أفكار.

  trends.py --tiktok "كرتون,قصص_اطفال" --youtube "كرتون قصير|stick figure animation" --per 10 --budget 0.5 -o reports/

- المفتاح: يحقنه وكيل الشبكة في الطلبات إلى api.apify.com (لا متغير بيئة). على جهاز آخر: APIFY_TOKEN=... .
- الأدوات: clockworks/tiktok-scraper (هاشتاغات) و streamers/youtube-scraper (بحث شورتس، ترتيب بالمشاهدات).
- التكلفة تقريبية: ~0.004$ لكل مقطع + 0.001$ لكل تشغيل. السكربت يرفض التشغيل إن تجاوز التقدير --budget.
- الترتيب: مشاهدات/يوم منذ النشر (قوة الرواج) ثم نسبة التفاعل (إعجاب+تعليق+مشاركة)/مشاهدة.
"""
import argparse, collections, datetime as dt, json, os, re, sys, urllib.request

API = 'https://api.apify.com/v2/acts/{}/run-sync-get-dataset-items?timeout=300'
PRICE = {'tiktok': 0.0037, 'youtube': 0.004}
START = 0.001
STOP = set('في من على الى إلى عن مع و ال the a an of to in for and with is on this that by'.split())


def run_actor(actor, payload):
    req = urllib.request.Request(API.format(actor.replace('/', '~')), data=json.dumps(payload).encode(), method='POST',
                                 headers={'Content-Type': 'application/json'})
    tok = os.environ.get('APIFY_TOKEN')
    if tok and tok != 'proxy-injected':
        req.add_header('Authorization', 'Bearer ' + tok)
    with urllib.request.urlopen(req, timeout=330) as r:
        return json.loads(r.read().decode())


def days_since(iso):
    try:
        t = dt.datetime.fromisoformat(str(iso).replace('Z', '+00:00'))
        return max(0.5, (dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 86400)
    except Exception:
        return None


def norm_tiktok(it):
    views = it.get('playCount') or 0
    eng = (it.get('diggCount') or 0) + (it.get('commentCount') or 0) + (it.get('shareCount') or 0)
    a = it.get('authorMeta') or {}
    return {'platform': 'TikTok', 'title': (it.get('text') or '').strip(), 'url': it.get('webVideoUrl'),
            'views': views, 'likes': it.get('diggCount') or 0, 'comments': it.get('commentCount') or 0,
            'shares': it.get('shareCount') or 0, 'eng': eng, 'author': a.get('name'), 'followers': a.get('fans'),
            'date': it.get('createTimeISO'), 'duration': (it.get('videoMeta') or {}).get('duration'),
            'tags': [h.get('name') for h in (it.get('hashtags') or []) if h.get('name')], 'source': it.get('_q')}


def norm_youtube(it):
    views = it.get('viewCount') or 0
    eng = (it.get('likes') or 0) + (it.get('commentsCount') or 0)
    title = it.get('title') or ''
    return {'platform': 'YouTube', 'title': title.strip(), 'url': it.get('url'), 'views': views,
            'likes': it.get('likes') or 0, 'comments': it.get('commentsCount') or 0, 'shares': 0, 'eng': eng,
            'author': it.get('channelName'), 'followers': it.get('numberOfSubscribers'), 'date': it.get('date'),
            'duration': it.get('duration'), 'tags': re.findall(r'#(\w+)', title + ' ' + (it.get('text') or '')),
            'source': it.get('input') or it.get('_q')}


def score(v):
    d = days_since(v['date'])
    v['days'] = round(d, 1) if d else None
    v['vpd'] = round(v['views'] / d) if d else v['views']
    v['er'] = round(100 * v['eng'] / v['views'], 1) if v['views'] else 0
    return v


def words(texts):
    c = collections.Counter()
    for t in texts:
        for w in re.findall(r'[\w؀-ۿ]{3,}', re.sub(r'#\w+|https?://\S+', ' ', t.lower())):
            if w not in STOP and not w.isdigit():
                c[w] += 1
    return c


def fmt(n):
    n = n or 0
    return f'{n / 1e6:.1f}M' if n >= 1e6 else f'{n / 1e3:.0f}K' if n >= 1e3 else str(n)


def report(vids, args, cost):
    today = dt.date.today().isoformat()
    vids = sorted(vids, key=lambda v: (v['vpd'], v['er']), reverse=True)
    L = [f'# تقرير المقاطع الرائجة — {today}', '',
         f'- تيك توك (هاشتاغات): {args.tiktok or "—"}', f'- يوتيوب (بحث شورتس): {args.youtube or "—"}',
         f'- عدد المقاطع: {len(vids)} — التكلفة التقديرية: ~{cost:.2f}$ من رصيد Apify', '',
         '## أقوى المقاطع (مرتبة بالمشاهدات اليومية)', '',
         '| # | المنصة | المشاهدات | يومياً | التفاعل | المدة | العنوان | الرابط |', '|---|---|---|---|---|---|---|---|']
    for k, v in enumerate(vids[:args.top], 1):
        t = re.sub(r'\s+', ' ', v['title'])[:70].replace('|', '/')
        L.append(f"| {k} | {v['platform']} | {fmt(v['views'])} | {fmt(v['vpd'])} | {v['er']}% | {v['duration'] or ''} | {t} | [رابط]({v['url']}) |")
    tags = collections.Counter(t.lower() for v in vids for t in v['tags'])
    L += ['', '## الهاشتاغات الأكثر تكراراً في المقاطع القوية', '',
          '، '.join(f'#{t} ({n})' for t, n in tags.most_common(20)) or '—', '',
          '## الكلمات المتكررة في العناوين (مؤشر على المواضيع)', '',
          '، '.join(f'{w} ({n})' for w, n in words(v['title'] for v in vids[:max(10, len(vids) // 2)]).most_common(25)) or '—', '',
          '## ملاحظات للتحليل', '',
          '- «يومياً» = المشاهدات ÷ الأيام منذ النشر: الأعلى هو الرائج الآن، لا القديم المتراكم.',
          '- «التفاعل» = (إعجاب + تعليق + مشاركة) ÷ مشاهدات: فوق 5% مؤشر قوي على محتوى يحبه الجمهور.',
          '- اقرأ أعلى 10 عناوين وابحث عن النمط المشترك (موقف، شخصية، مفاجأة، طول المقطع).', '']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tiktok', default='', help='هاشتاغات تيك توك مفصولة بفواصل (بلا #)')
    ap.add_argument('--youtube', default='', help='عبارات بحث يوتيوب مفصولة بـ |')
    ap.add_argument('--per', type=int, default=10, help='عدد المقاطع لكل هاشتاغ/بحث')
    ap.add_argument('--date', default='month', choices=['week', 'month', 'year'], help='فترة يوتيوب')
    ap.add_argument('--budget', type=float, default=0.5, help='حد التكلفة بالدولار لهذا التشغيل')
    ap.add_argument('--top', type=int, default=25)
    ap.add_argument('-o', default='reports')
    a = ap.parse_args()
    tt = [h.strip().lstrip('#') for h in a.tiktok.split(',') if h.strip()]
    yt = [q.strip() for q in a.youtube.split('|') if q.strip()]
    est = len(tt) * a.per * PRICE['tiktok'] + len(yt) * a.per * PRICE['youtube'] + START * (bool(tt) + bool(yt))
    print(f'  التكلفة التقديرية: ~{est:.3f}$ (الحد {a.budget}$)', file=sys.stderr)
    if est > a.budget:
        sys.exit(f'  ✗ التقدير يتجاوز الحد. قلّل --per أو عدد الهاشتاغات، أو ارفع --budget.')
    vids = []
    if tt:
        items = run_actor('clockworks/tiktok-scraper', {'hashtags': tt, 'resultsPerPage': a.per,
                          'shouldDownloadVideos': False, 'shouldDownloadCovers': False, 'shouldDownloadAvatars': False})
        vids += [score(norm_tiktok(i)) for i in items if i.get('playCount') is not None]
        print(f'  تيك توك: {len(items)} مقطع', file=sys.stderr)
    if yt:
        items = run_actor('streamers/youtube-scraper', {'searchQueries': yt, 'maxResults': 0, 'maxResultsShorts': a.per,
                          'maxResultStreams': 0, 'sortingOrder': 'views', 'dateFilter': a.date})
        vids += [score(norm_youtube(i)) for i in items if i.get('viewCount') is not None]
        print(f'  يوتيوب: {len(items)} مقطع', file=sys.stderr)
    os.makedirs(a.o, exist_ok=True)
    stamp = dt.datetime.now().strftime('%Y-%m-%d')
    md, js = os.path.join(a.o, f'trends-{stamp}.md'), os.path.join(a.o, f'trends-{stamp}.json')
    open(md, 'w', encoding='utf-8').write(report(vids, a, est))
    json.dump(vids, open(js, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(md)


if __name__ == '__main__':
    main()
