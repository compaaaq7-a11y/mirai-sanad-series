"""«القصة الحقيقية»: نسخة بلقطات حقيقية لحيوانات حقيقية من كل حلقة ثلاثية الأبعاد، بالتعليق نفسه.

لكل مشهد قائمة كلمات بحث؛ نأخذ من Pixabay (مجاني، بلا حاجة لنسب) أنسب مقطع لم يُستخدم بعد،
نقصّه على مدة اللقطة ونحوّله إلى 1080x1920، ثم نضع صوت الحلقة (التعليق + المؤثرات + الموسيقى).

    PIXABAY_API_KEY=... python real/real_episode.py ep06
    (الصوت أولاً: python blender/finish.py --ep ep06 audio)
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (من، إلى، [كلمات بحث بالأفضلية]) — اللقطات تتبع جمل التعليق
SHOTS = {
    "ep06": [  # سند وميراي ينقذان الفرخ الصغير (الجمل: 0.9، 6.3، 12.7، 17.6، 23.4)
        (0.0, 2.8, ["sunny garden tree", "garden trees sunlight", "green park tree"], ("tree", "garden", "park")),
        (2.8, 6.3, ["fledgling bird ground", "baby bird grass", "young sparrow ground", "baby sparrow"],
         ("fledgling", "chick", "sparrow", "baby bird", "young")),
        (6.3, 9.4, ["domestic cat crouching grass", "house cat stalking garden", "cat sneaking grass", "cat garden"],
         ("cat", "kitten")),
        (9.4, 12.7, ["cat eyes close up", "orange cat staring", "ginger cat face"], ("cat", "kitten")),
        (12.7, 17.4, ["kitten playing ball", "cat playing toy", "kitten playing yarn"], ("cat", "kitten")),
        (17.4, 20.8, ["hands holding small bird", "holding baby bird", "bird in hand"], ("hand", "hands")),
        (20.8, 23.3, ["bird nest tree branch", "bird nest", "nest with chicks"], ("nest",)),
        (23.3, 27.0, ["bird feeding chicks nest", "mother bird feeding babies", "birds nest chicks feeding"],
         ("nest", "chicks", "chick", "fledglings")),
        (27.0, 30.0, ["bird flying slow motion", "bird flying tree", "bird flight"], ("flying", "flight", "fly")),
    ],
    "ep07": [  # أول رحلة للعصفور
        (0.0, 4.6, ["tree branch sunny", "garden tree sunlight", "spring tree leaves"]),
        (4.6, 9.3, ["young bird nest", "fledgling nest", "baby bird nest"]),
        (9.3, 13.6, ["fledgling branch", "young bird branch", "bird hopping branch"]),
        (13.6, 18.5, ["bird flapping wings", "bird taking off", "bird flying slow motion"]),
        (18.5, 23.0, ["bird flying meadow", "bird flight flowers", "bird flying"]),
        (23.0, 30.0, ["two birds flying", "birds flying sky", "birds on fence"]),
    ],
    "part3": [  # القطة العالقة
        (0.0, 5.6, ["birds chirping tree", "bird singing branch", "birds tree"]),
        (5.6, 10.6, ["cat in tree", "cat on tree branch", "kitten tree"]),
        (10.6, 15.6, ["wooden box garden", "kitten playing yarn", "ball of yarn"]),
        (15.6, 19.5, ["cat jumping", "cat jump slow motion", "kitten jumping"]),
        (19.5, 23.3, ["holding cat arms", "hugging cat", "person holding kitten"]),
        (23.3, 30.0, ["kitten playing yarn ball", "cat playing grass", "cat and birds garden"]),
    ],
    "part4": [  # جرس البقرة
        (0.0, 4.0, ["cow walking meadow", "cow walking grass", "cow pasture"]),
        (4.0, 8.0, ["cow face close up", "cow looking camera", "cow head"]),
        (8.0, 10.8, ["cow grazing", "cow eating grass", "cows field"]),
        (10.8, 15.4, ["kitten playing grass", "cat playing flowers", "cat paw playing"]),
        (15.4, 18.2, ["cow bell", "cowbell", "bell ringing"]),
        (18.2, 22.6, ["cow with bell", "cow bell neck", "alpine cow bell"]),
        (22.6, 26.0, ["cow mooing", "cow close up", "happy cow"]),
        (26.0, 30.0, ["cow walking away", "cows walking pasture", "cow herd walking"]),
    ],
}
OUT_NAME = {"ep06": "real-ep06-baby-bird.mp4", "ep07": "real-ep07-first-flight.mp4",
            "part3": "real-part3-stuck-cat.mp4", "part4": "real-part4-cow-bell.mp4"}


def log(m):
    print(m, flush=True)


HEADERS = {"User-Agent": "mirai-sanad-series/1.0 (real-footage episode builder)"}


def get(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        where = url.split("?")[0]
        sys.exit(f"خطأ {e.code} من {where}: {body}")


def search(key, q):
    url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode(
        {"key": key, "q": q, "safesearch": "true", "per_page": 20, "order": "popular"})
    with get(url) as r:
        return json.load(r).get("hits", [])


# وسوم تُستبعد دائماً: حيوانات مفترسة أو مشاهد مخيفة، ومحتوى مولّد بالذكاء الاصطناعي (القصة «حقيقية»)
BLOCK = {"lion", "lioness", "tiger", "leopard", "predator", "roar", "wolf", "bear", "blood", "dead", "hunt",
         "ai", "ai generated", "generated", "artificial intelligence", "animation", "cartoon", "3d", "render"}


def tags_of(h):
    return {t.strip().lower() for t in h.get("tags", "").split(",") if t.strip()}


def pick(key, queries, need, used, must=()):
    for q in queries:
        for h in search(key, q):
            if h["id"] in used or h.get("duration", 0) < need + 0.3:
                continue
            tags = tags_of(h)
            words = {w for t in tags for w in t.split()}
            if tags & BLOCK or words & {"lion", "lioness", "tiger", "ai", "generated", "animation", "cartoon"}:
                continue
            if must and not any(m in words or m in tags for m in must):
                continue
            v = h["videos"]
            best = next((v[s] for s in ("large", "medium") if v.get(s, {}).get("url") and v[s]["height"] >= 720), None)
            if best:
                used.add(h["id"])
                return q, h, best
    return None


def main():
    ep = sys.argv[1]
    key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not key:
        sys.exit("PIXABAY_API_KEY غير موجود")
    build = ROOT / "build" / f"real-{ep}"
    build.mkdir(parents=True, exist_ok=True)
    used, parts, credits = set(), [], []
    for i, shot in enumerate(SHOTS[ep]):
        t0, t1, queries = shot[:3]
        must = shot[3] if len(shot) > 3 else ()
        need = t1 - t0
        found = pick(key, queries, need, used, must)
        if not found:
            sys.exit(f"لا يوجد مقطع مناسب للقطة {i} ({queries})")
        q, hit, vid = found
        raw = build / f"raw{i}.mp4"
        with get(vid["url"]) as r:
            raw.write_bytes(r.read())
        start = max(0.0, min(hit["duration"] - need - 0.2, hit["duration"] * 0.2))
        out = build / f"shot{i}.mp4"
        # قصّ مركزي إلى 9:16 بدقة 1080x1920، 30 إطاراً، بلا صوت، مع تلاشٍ قصير عند الأطراف
        vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,"
              f"fade=t=in:st=0:d=0.25,fade=t=out:st={need - 0.25:.2f}:d=0.25,format=yuv420p")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.2f}", "-i", str(raw), "-t", f"{need:.3f}",
                        "-vf", vf, "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18", str(out)], check=True)
        parts.append(out)
        credits.append({"shot": i, "from": t0, "to": t1, "query": q, "pixabay": hit.get("pageURL"),
                        "user": hit.get("user")})
        log(f"لقطة {i} ({t0}-{t1}): «{q}» -> {hit.get('pageURL')}")
    lst = build / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
    silent = build / "silent.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                    str(silent)], check=True)
    audio = ROOT / "build" / ep / "audio.wav"
    out = ROOT / "output" / OUT_NAME[ep]
    out.parent.mkdir(exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(audio), "-map", "0:v", "-map", "1:a",
                    "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1", "-pix_fmt", "yuv420p", "-crf", "18",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)],
                   check=True)
    (ROOT / "output" / (OUT_NAME[ep][:-4] + ".json")).write_text(json.dumps(credits, ensure_ascii=False, indent=1),
                                                                 encoding="utf-8")
    log(f"تم: {out}")


if __name__ == "__main__":
    main()
