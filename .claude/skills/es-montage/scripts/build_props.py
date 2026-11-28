"""Merge brand.json + cuts.json + words.json into the Remotion props.

- applies extra "remove" ranges from brand.json (source time) to the kept segments
- maps every word to output time and groups words into caption chunks
- copies source.mp4 (and the music) into template/public/
- writes template/src/montage.json and <work>/final.srt

usage: build_props.py WORK_DIR
"""
import json
import shutil
import sys
from pathlib import Path

FPS, W, H = 30, 1080, 1920
PUNCT = tuple(".!?؟،,؛:…")

# Windows consoles default to a legacy codepage
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def load(path, default=None):
    if not path.exists():
        if default is not None:
            return default
        raise SystemExit(f"missing {path.name} - run the earlier steps first")
    return json.loads(path.read_text(encoding="utf-8"))


def subtract(keep, remove):
    out = [list(s) for s in keep]
    for rs, re_ in remove:
        nxt = []
        for s, e in out:
            if re_ <= s or rs >= e:
                nxt.append([s, e])
                continue
            if rs - s >= 0.1:
                nxt.append([s, rs])
            if e - re_ >= 0.1:
                nxt.append([re_, e])
        out = nxt
    return out


def to_output(t, segments):
    for seg in segments:
        if seg["from"] <= t <= seg["to"]:
            return seg["outStart"] + (t - seg["from"])
    return None


def group(words, max_words, max_dur=2.0, max_gap=0.4):
    chunks, cur = [], []
    for w in words:
        if cur:
            prev = cur[-1]
            if (len(cur) >= max_words or w["start"] - prev["end"] > max_gap
                    or w["end"] - cur[0]["start"] > max_dur or prev["text"].endswith(PUNCT)):
                chunks.append(cur)
                cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    caps = []
    for i, c in enumerate(chunks):
        end = c[-1]["end"] + 0.25
        if i + 1 < len(chunks):
            end = min(end, chunks[i + 1][0]["start"])
        caps.append({"start": round(c[0]["start"], 3), "end": round(end, 3), "words": c})
    return caps


def face_layout(cuts, segments, hook_seconds):
    """Face boxes from cuts.json (fractions of the source, over time) -> pixels on the 1080x1920
    canvas, using the same cover-crop as the template. Returns what the layout needs:
    the head during the hook, its typical spot (for captions), and a zoom center per part."""
    faces, size = cuts.get("faces") or [], cuts.get("size")
    if not faces or not size:
        return None, [None] * len(segments)
    pw, ph = size
    s = max(W / pw, H / ph)
    ox, oy = (pw * s - W) / 2, (ph * s - H) / 2
    px = lambda f: {"x0": f["x0"] * pw * s - ox, "y0": f["y0"] * ph * s - oy,
                    "x1": f["x1"] * pw * s - ox, "y1": f["y1"] * ph * s - oy}
    median = lambda vals: sorted(vals)[len(vals) // 2]
    mid_box = lambda bs: {k: median([b[k] for b in bs]) for k in ("x0", "y0", "x1", "y1")}
    clean = lambda b: {k: round(min(W if k[0] == "x" else H, max(0, v))) for k, v in b.items()}

    # each detection on the edited timeline (dropped if its moment was cut)
    timed = []
    for f in faces:
        seg = next((g for g in segments if g["from"] <= f["t"] <= g["to"]), None)
        if seg:
            timed.append((seg["outStart"] + f["t"] - seg["from"], seg, px(f)))
    if not timed:
        return None, [None] * len(segments)

    during_hook = [b for t, _, b in timed if t <= hook_seconds + 0.3] or [min(timed, key=lambda x: x[0])[2]]
    hook_box = {"x0": min(b["x0"] for b in during_hook), "y0": min(b["y0"] for b in during_hook),
                "x1": max(b["x1"] for b in during_hook), "y1": max(b["y1"] for b in during_hook)}
    typical = mid_box([b for _, _, b in timed])

    origins = []
    for g in segments:
        bs = [b for _, seg, b in timed if seg is g]
        c = mid_box(bs) if bs else typical
        origins.append([round((c["x0"] + c["x1"]) / 2), round((c["y0"] + c["y1"]) / 2)])
    return {"hook": clean(hook_box), "typical": clean(typical)}, origins


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    work = Path(sys.argv[1])
    skill_dir = Path(__file__).resolve().parent.parent
    brand = {**load(skill_dir / "brand.example.json"), **load(work / "brand.json", {})}
    brand.pop("_help", None)
    cuts = load(work / "cuts.json")
    words = load(work / "words.json")["words"]

    keep = subtract(cuts["keep"], brand.get("remove") or [])
    segments, out_t = [], 0.0
    for s, e in keep:
        # snap to whole frames so video and captions never drift
        fs, fe = round(s * FPS), round(e * FPS)
        if fe - fs < 3:
            continue
        segments.append({"from": fs / FPS, "to": fe / FPS, "outStart": round(out_t, 4)})
        out_t += (fe - fs) / FPS
    if not segments:
        raise SystemExit("nothing left to keep - check cuts.json / remove ranges")

    mapped = []
    for w in words:
        # Whisper's edges are loose, so match by overlap rather than by midpoint
        overlap = lambda g: min(w["end"], g["to"]) - max(w["start"], g["from"])
        seg = max(segments, key=overlap)
        dur = max(0.01, w["end"] - w["start"])
        if overlap(seg) < min(0.08, dur * 0.3):
            continue  # the word was in a removed part
        s = max(w["start"], seg["from"])
        e = min(w["end"], seg["to"])
        mapped.append({"text": w["text"], "start": round(to_output(s, segments), 3),
                       "end": round(to_output(e, segments), 3)})

    captions = group(mapped, int(brand.get("maxWordsPerCaption", 3)))

    template = work / "template"
    public = template / "public"
    public.mkdir(parents=True, exist_ok=True)
    src, dst = work / cuts["source"], public / "source.mp4"
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, dst)

    music = None
    if brand.get("music"):
        mp = Path(brand["music"])
        if not mp.is_absolute():
            mp = work / mp
        if not mp.exists():
            raise SystemExit(f"music file not found: {mp}")
        music = "music" + mp.suffix.lower()
        shutil.copy2(mp, public / music)

    face, origins = face_layout(cuts, segments, float(brand.get("hookSeconds", 2.6)) if brand.get("hook") else 0)
    for g, o in zip(segments, origins):
        g["zoomOrigin"] = o

    props = {
        "fps": FPS, "width": W, "height": H,
        "durationInFrames": max(1, round(out_t * FPS)),
        "video": "source.mp4",
        "segments": segments,
        "captions": captions,
        "music": music,
        "face": face,
        "brand": brand,
    }
    (template / "src" / "montage.json").write_text(
        json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")

    srt = []
    for i, c in enumerate(captions, 1):
        text = " ".join(w["text"] for w in c["words"])
        srt.append(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{text}\n")
    (work / "final.srt").write_text("\n".join(srt), encoding="utf-8")

    print(f"{len(segments)} parts, {out_t:.1f}s, {len(mapped)} words in {len(captions)} captions")
    print(f"wrote {template / 'src' / 'montage.json'} and {work / 'final.srt'}")


if __name__ == "__main__":
    main()
