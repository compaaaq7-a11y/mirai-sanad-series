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
    "ep07": [  # أول رحلة للعصفور (الجمل: 0.6، 5.0، 9.5، 14.2، 23.0)
        (0.0, 5.0, ["tree branch sunny", "garden tree sunlight", "spring tree leaves"], ("tree", "branch", "garden")),
        (5.0, 9.4, ["young bird nest", "fledgling nest", "baby bird nest", "chicks nest"],
         ("nest", "fledgling", "chicks", "chick")),
        (9.4, 14.1, ["fledgling branch", "young bird branch", "bird hopping branch", "sparrow branch"],
         ("branch", "fledgling", "sparrow", "young")),
        (14.1, 18.5, ["bird flapping wings", "bird taking off", "bird flying slow motion"],
         ("flapping", "wings", "flying", "flight", "takeoff")),
        (18.5, 23.0, ["small bird flying", "sparrow flying", "bird flight flowers"], ("flying", "flight", "fly")),
        (23.0, 30.0, ["two birds branch", "birds together branch", "birds flying sky"],
         ("birds", "pair", "couple", "flying")),
    ],
    "part3": [  # القطة العالقة (الجمل: 0.5، 5.7، 10.7، 16.4، 23.2)
        (0.0, 5.7, ["birds chirping tree", "bird singing branch", "birds tree branch"], ("bird", "birds", "songbird")),
        (5.7, 10.6, ["cat climbing tree", "cat sitting in tree", "cat tree branch", "kitten climbing", "cat on roof"],
         ("cat", "kitten")),
        (10.6, 15.5, ["kitten playing yarn", "ball of yarn", "wool yarn ball", "cat yarn"],
         ("yarn", "wool", "ball", "kitten", "cat")),
        (15.5, 19.5, ["cat jumping", "cat jump slow motion", "kitten jumping"], ("cat", "kitten", "jump", "jumping")),
        (19.5, 23.2, ["woman holding cat", "girl holding cat", "cat in arms", "hugging cat", "holding kitten"],
         ("cat", "kitten")),
        (23.2, 30.0, ["kitten playing grass", "cat playing garden", "cat playing toy"], ("cat", "kitten")),
    ],
    "part4": [  # جرس البقرة (الجمل: 0.6، 10.8، 15.4، 18.2، 23.7)
        (0.0, 4.0, ["cow walking meadow", "cow walking grass", "cow pasture"], ("cow", "cows", "cattle")),
        (4.0, 8.0, ["cow face close up", "cow looking camera", "cow head"], ("cow", "cows", "cattle")),
        (8.0, 10.8, ["cow grazing", "cow eating grass", "cows field"], ("cow", "cows", "cattle", "grazing")),
        (10.8, 15.4, ["kitten playing grass", "cat playing flowers", "cat paw playing"], ("cat", "kitten")),
        (15.4, 18.2, ["cow bell", "cowbell", "bell swinging"], ("bell", "cowbell")),
        (18.2, 22.6, ["cow with bell", "cow bell neck", "alpine cow bell"], ("bell", "cowbell", "cow")),
        (22.6, 26.0, ["happy cow", "cow close up", "calf cow"], ("cow", "calf", "cattle")),
        (26.0, 30.0, ["cow walking away", "cows walking pasture", "cow herd walking"], ("cow", "cows", "cattle")),
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
         "ai", "ai generated", "generated", "artificial intelligence", "animation", "cartoon", "3d", "render",
         "cigarette", "smoke", "smoking", "tobacco", "cigar", "vape", "alcohol", "beer", "wine", "drink",
         "gun", "weapon", "knife", "war", "fire", "injury", "sad", "cage", "slaughter", "meat"}
BLOCK_WORDS = {"lion", "lioness", "tiger", "ai", "generated", "animation", "cartoon", "cigarette", "smoking",
               "smoke", "tobacco", "alcohol", "beer", "wine", "gun", "weapon", "knife", "blood", "meat"}


def tags_of(h):
    return {t.strip().lower() for t in h.get("tags", "").split(",") if t.strip()}


def pick(key, queries, need, used, must=()):
    for q in queries:
        for h in search(key, q):
            if h["id"] in used or h.get("duration", 0) < need + 0.3:
                continue
            tags = tags_of(h)
            words = {w for t in tags for w in t.split()}
            if tags & BLOCK or words & BLOCK_WORDS:
                continue
            if must and not any(m in words or m in tags for m in must):
                continue
            v = h["videos"]
            best = next((v[s] for s in ("large", "medium") if v.get(s, {}).get("url") and v[s]["height"] >= 720), None)
            if best:
                used.add(h["id"])
                return q, h, best
    return None


def ok_hit(h, need, must):
    tags = tags_of(h)
    words = {w for t in tags for w in t.split()}
    if h.get("duration", 0) < need + 0.3 or tags & BLOCK or words & BLOCK_WORDS:
        return False
    return not must or any(m in words or m in tags for m in must)


def candidates(ep, key, per_shot=6):
    """لوحة مرشّحين لكل لقطة: كل صف مقطع واحد بثلاث صور (ربع/نصف/ثلاثة أرباع)، للمراجعة البشرية."""
    out = ROOT / "output" / f"real-candidates-{ep}"
    out.mkdir(parents=True, exist_ok=True)
    info = {}
    for i, shot in enumerate(SHOTS[ep]):
        t0, t1, queries = shot[:3]
        must = shot[3] if len(shot) > 3 else ()
        need = t1 - t0
        seen, rows = set(), []
        for q in queries:
            for h in search(key, q):
                if h["id"] in seen or not ok_hit(h, need, must):
                    continue
                seen.add(h["id"])
                rows.append((q, h))
                if len(rows) >= per_shot:
                    break
            if len(rows) >= per_shot:
                break
        info[i] = []
        imgs = []
        for j, (q, h) in enumerate(rows):
            v = h["videos"]
            small = next((v[k] for k in ("tiny", "small", "medium") if v.get(k, {}).get("url")), None)
            if not small:
                continue
            tmp = out / f"tmp_{i}_{j}.mp4"
            with get(small["url"]) as r:
                tmp.write_bytes(r.read())
            d = h["duration"]
            row = out / f"row_{i}_{j}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y"] + sum((["-ss", f"{d * f:.2f}", "-i", str(tmp)] for f in (0.25, 0.5, 0.75)), [])
                           + ["-filter_complex", "[0]scale=-2:180,trim=end_frame=1[a];[1]scale=-2:180,trim=end_frame=1[b];"
                              "[2]scale=-2:180,trim=end_frame=1[c];[a][b][c]hstack=3,pad=iw+20:ih+10:20:5:white",
                              "-frames:v", "1", str(row)], check=True)
            tmp.unlink()
            imgs.append(row)
            info[i].append({"row": len(imgs) - 1, "id": h["id"], "query": q, "duration": d, "tags": h.get("tags"),
                            "page": h.get("pageURL")})
        if imgs:
            ins = sum((["-i", str(p)] for p in imgs), [])
            subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex",
                           "".join(f"[{k}]scale=640:-2[r{k}];" for k in range(len(imgs))) +
                           "".join(f"[r{k}]" for k in range(len(imgs))) + f"vstack={len(imgs)}" if len(imgs) > 1 else "[0]scale=640:-2",
                           "-frames:v", "1", str(out / f"shot{i}.png")], check=True)
            for p in imgs:
                p.unlink()
        log(f"لقطة {i}: {len(imgs)} مرشّح")
    (out / "candidates.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")


def by_id(key, vid_id):
    url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": key, "id": vid_id})
    with get(url) as r:
        hits = json.load(r).get("hits", [])
    if not hits:
        sys.exit(f"المقطع {vid_id} غير موجود")
    return hits[0]


def main():
    ep = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "build"
    key = os.environ.get("PIXABAY_API_KEY", "").strip()
    if not key:
        sys.exit("PIXABAY_API_KEY غير موجود")
    if mode == "candidates":
        candidates(ep, key)
        return
    picks_file = ROOT / "real" / "picks" / f"{ep}.json"
    picks = json.loads(picks_file.read_text(encoding="utf-8")) if picks_file.exists() else {}
    build = ROOT / "build" / f"real-{ep}"
    build.mkdir(parents=True, exist_ok=True)
    used, parts, credits = set(), [], []
    for i, shot in enumerate(SHOTS[ep]):
        t0, t1, queries = shot[:3]
        must = shot[3] if len(shot) > 3 else ()
        need = t1 - t0
        if str(i) in picks:  # مقطع اختير بعد مراجعة بشرية للوحة المرشّحين
            h = by_id(key, picks[str(i)])
            v = h["videos"]
            best = next((v[k] for k in ("large", "medium") if v.get(k, {}).get("url") and v[k]["height"] >= 720), None)
            found = ("اختيار يدوي", h, best) if best else None
        else:
            sys.exit(f"اللقطة {i} بلا اختيار في {picks_file.name}؛ شغّل وضع candidates وراجع اللوحات أولاً")
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
