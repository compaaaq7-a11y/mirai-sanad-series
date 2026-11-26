#!/usr/bin/env python3
"""سلسلة ميراي سند: توليد حلقات الفيديو بأداة MoneyPrinterTurbo.

الاستخدام:
    python3 mirai.py setup                 # تنزيل الأداة وتثبيتها (مرة واحدة)
    python3 mirai.py list                  # عرض الحلقات
    python3 mirai.py generate              # توليد كل الحلقات
    python3 mirai.py generate ep01-intro   # توليد حلقة واحدة أو أكثر
    python3 mirai.py generate --source local   # استخدام لقطات من مجلد assets/
    python3 mirai.py publish               # نشر الحلقات الجاهزة على قناة يوتيوب

متغيرات البيئة الاختيارية:
    PIXABAY_API_KEY مفتاح Pixabay المجاني للقطات الفيديو (موصى به)
    PEXELS_API_KEY  مفتاح Pexels (إصدار مفاتيحه الجديدة متوقف حالياً)
    COVERR_API_KEY  مفتاح Coverr
    بدون أي مفتاح تُستخدم اللقطات الموجودة في assets/
    MPT_DIR         مكان MoneyPrinterTurbo (الافتراضي vendor/MoneyPrinterTurbo)
    YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN  صلاحية النشر على قناة يوتيوب
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERIES_FILE = ROOT / "series.toml"
ASSETS_DIR = ROOT / "assets"
OUTPUT_DIR = ROOT / "output"
BUILD_DIR = ROOT / "build"
MPT_REPO = "https://github.com/harry0703/MoneyPrinterTurbo.git"
MPT_DIR = Path(os.environ.get("MPT_DIR", ROOT / "vendor" / "MoneyPrinterTurbo")).resolve()
ARABIC_FONT = "Cairo-Regular.ttf"
MEDIA_EXT = {".mp4", ".mov", ".mkv", ".webm", ".jpg", ".jpeg", ".png", ".webp"}


def log(msg: str) -> None:
    print(f"[ميراي سند] {msg}", file=sys.stderr, flush=True)


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    log("$ " + " ".join(cmd))
    return subprocess.run(cmd, check=True, **kw)


# ---------------------------------------------------------------- setup
def setup(_args=None) -> None:
    if shutil.which("ffmpeg") is None:
        log("تحذير: ffmpeg غير مثبت. ثبّته أولاً (مثلاً: sudo apt install ffmpeg)")
    if not (MPT_DIR / "cli.py").exists():
        MPT_DIR.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--depth", "1", MPT_REPO, str(MPT_DIR)])
    if shutil.which("uv") is None:
        run([sys.executable, "-m", "pip", "install", "--user", "uv"])
    run([uv(), "sync"], cwd=MPT_DIR)
    install_arabic_font()
    write_config()
    log(f"تم التثبيت في {MPT_DIR}")


def uv() -> str:
    found = shutil.which("uv")
    if found:
        return found
    local = Path.home() / ".local" / "bin" / "uv"
    if local.exists():
        return str(local)
    sys.exit("لم يُعثر على uv. شغّل: python3 -m pip install uv")


def install_arabic_font() -> None:
    target = MPT_DIR / "resource" / "fonts" / ARABIC_FONT
    if target.exists():
        return
    fonts = list((MPT_DIR / ".venv").glob(f"lib/python*/site-packages/khatt/fonts/{ARABIC_FONT}"))
    fonts += list((MPT_DIR / ".venv").glob(f"Lib/site-packages/khatt/fonts/{ARABIC_FONT}"))
    if fonts:
        shutil.copy2(fonts[0], target)
        log(f"ثُبّت الخط العربي {ARABIC_FONT}")
    else:
        log("لم يُعثر على الخط العربي؛ ستستخدم الأداة خطها الاحتياطي")


# مصادر اللقطات المجانية بترتيب الأفضلية: (اسم المصدر، متغير البيئة)
STOCK_SOURCES = [("pixabay", "PIXABAY_API_KEY"), ("pexels", "PEXELS_API_KEY"), ("coverr", "COVERR_API_KEY")]


def write_config() -> None:
    """أنشئ config.toml للأداة وضع فيه مفاتيح اللقطات الموجودة في البيئة."""
    config = MPT_DIR / "config.toml"
    if not config.exists():
        shutil.copy2(MPT_DIR / "config.example.toml", config)
    text = config.read_text(encoding="utf-8")
    for source, env in STOCK_SOURCES:
        key = os.environ.get(env, "").strip()
        if key:
            text = re.sub(rf"(?m)^{source}_api_keys\s*=.*$",
                          lambda _m: f"{source}_api_keys = {json.dumps([key])}", text, count=1)
            log(f"أُضيف مفتاح {source} إلى الإعدادات")
    config.write_text(text, encoding="utf-8")


def configured_source() -> str:
    """أول مصدر لقطات له مفتاح، وإلا local."""
    config = MPT_DIR / "config.toml"
    app = tomllib.loads(config.read_text(encoding="utf-8")).get("app", {}) if config.exists() else {}
    for source, env in STOCK_SOURCES:
        if os.environ.get(env, "").strip() or app.get(f"{source}_api_keys"):
            return source
    return "local"


# ---------------------------------------------------------------- series
def load_series() -> dict:
    data = tomllib.loads(SERIES_FILE.read_text(encoding="utf-8"))
    ids = [ep["id"] for ep in data.get("episodes", [])]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f"أسماء حلقات مكررة: {', '.join(sorted(dupes))}")
    return data


def list_episodes(_args=None) -> None:
    for ep in load_series()["episodes"]:
        words = len(ep["script"].split())
        print(f"{ep['id']:<20} {ep.get('title', '')}  (~{words} كلمة)")


def local_materials() -> list[dict]:
    ASSETS_DIR.mkdir(exist_ok=True)
    files = sorted(p for p in ASSETS_DIR.iterdir() if p.suffix.lower() in MEDIA_EXT)
    if not files:
        fallback = BUILD_DIR / "fallback-bg.mp4"
        if not fallback.exists():
            BUILD_DIR.mkdir(exist_ok=True)
            log("مجلد assets/ فارغ؛ سأنشئ خلفية ملونة بسيطة")
            run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi",
                 "-i", "color=c=0x0b3d5c:s=1080x1920:d=10,format=yuv420p", str(fallback)])
        files = [fallback]
    return [{"provider": "local", "url": str(p.resolve())} for p in files]


def build_manifest(episodes: list[dict], defaults: dict, source: str, voice: str | None) -> Path:
    materials = local_materials() if source == "local" else None
    lines = []
    for ep in episodes:
        task = dict(defaults)
        task.update({k: v for k, v in ep.items() if k not in {"id", "title", "script", "terms", "approved"}})
        task["video_subject"] = ep.get("title", ep["id"])
        task["video_script"] = " ".join(ep["script"].split())
        task["video_source"] = source
        if voice:
            task["voice_name"] = voice
        if source == "local":
            task["video_materials"] = materials
            task.pop("video_terms", None)
        elif ep.get("terms"):
            task["video_terms"] = [t.strip() for t in ep["terms"].split(",") if t.strip()]
        lines.append(json.dumps(task, ensure_ascii=False))
    BUILD_DIR.mkdir(exist_ok=True)
    manifest = BUILD_DIR / "manifest.jsonl"
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def generate(args) -> int:
    if not (MPT_DIR / "cli.py").exists():
        setup()
    else:
        install_arabic_font()
        write_config()

    series = load_series()
    episodes = series["episodes"]
    if args.episodes:
        wanted = set(args.episodes)
        unknown = wanted - {ep["id"] for ep in episodes}
        if unknown:
            sys.exit(f"حلقات غير موجودة: {', '.join(sorted(unknown))}")
        episodes = [ep for ep in episodes if ep["id"] in wanted]

    source = args.source or configured_source()
    log(f"مصدر اللقطات: {source}")
    manifest = build_manifest(episodes, series.get("defaults", {}), source, args.voice)
    log(f"سيتم توليد {len(episodes)} حلقة")

    cmd = [uv(), "run", "python", "cli.py", "--batch-file", str(manifest)]
    proc = subprocess.run(cmd, cwd=MPT_DIR, stdout=subprocess.PIPE, text=True)
    try:
        summary = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        print(proc.stdout)
        log("تعذّر قراءة نتيجة الأداة")
        return proc.returncode or 1

    OUTPUT_DIR.mkdir(exist_ok=True)
    failed = 0
    for task in summary.get("tasks", []):
        index = task.get("index")  # الأداة ترقّم المهام بدءاً من 1
        ep = episodes[index - 1] if isinstance(index, int) and 1 <= index <= len(episodes) else None
        name = ep["id"] if ep else task.get("task_id")
        videos = (task.get("result") or {}).get("videos") or []
        if task.get("status") == "succeeded" and videos:
            dest = OUTPUT_DIR / f"{name}.mp4"
            shutil.copy2(videos[0], dest)
            if ep:
                write_metadata(ep, series)
            log(f"✓ {name} → {dest.relative_to(ROOT)}")
        else:
            failed += 1
            log(f"✗ {name}: فشل في مرحلة {task.get('failed_stage')}: {task.get('error')}")
    log(f"النتيجة: {summary.get('succeeded', 0)} نجحت، {failed} فشلت")
    return 1 if failed else 0

# ---------------------------------------------------------------- youtube
def episode_metadata(ep: dict, series: dict) -> dict:
    """عنوان ووصف ووسوم الحلقة كما تُنشر على يوتيوب."""
    info = series.get("series", {})
    channel = info.get("channel_url", "").rstrip("/")
    name = info.get("title", "")
    title = ep.get("title", ep["id"])
    full_title = f"{title} | {name}" if name else title
    lines = [title, "", ep["script"].strip(), ""]
    if channel:
        lines += [f"🔔 اشترك في {name} ليصلك كل جديد: {channel}?sub_confirmation=1",
                  f"📺 كل الحلقات: {channel}/videos", ""]
    # الفيديو العمودي (9:16) حتى 3 دقائق يضعه يوتيوب تلقائياً في Shorts
    short = ep.get("video_aspect", series.get("defaults", {}).get("video_aspect")) == "9:16"
    hashtags = ep.get("hashtags", info.get("hashtags", ""))
    lines.append(f"{hashtags} #Shorts".strip() if short else hashtags)
    tags = [x.strip() for x in ep.get("tags", info.get("tags", "")).split(",") if x.strip()]
    tags += ["Shorts"] if short else []
    tags += [title] + [x.strip() for x in ep.get("terms", "").split(",") if x.strip()]
    return {
        "title": full_title[:100],
        "description": "\n".join(lines).strip()[:5000],
        "tags": list(dict.fromkeys(tags)),
        "categoryId": str(ep.get("category_id", info.get("category_id", "27"))),
        "privacy": ep.get("privacy", info.get("privacy", "public")),
    }


def write_metadata(ep: dict, series: dict) -> None:
    meta = episode_metadata(ep, series)
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / f"{ep['id']}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def http(url: str, data: bytes | None = None, headers: dict | None = None, method: str | None = None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        return urllib.request.urlopen(req, timeout=600)
    except urllib.error.HTTPError as e:
        sys.exit(f"خطأ من يوتيوب ({e.code}): {e.read().decode('utf-8', 'replace')[:500]}")


def youtube_token() -> str:
    env = {k: os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")}
    missing = [k for k, v in env.items() if not v]
    if missing:
        sys.exit(f"لا توجد صلاحية نشر على يوتيوب؛ ينقص: {', '.join(missing)}")
    body = urllib.parse.urlencode({"client_id": env["YT_CLIENT_ID"], "client_secret": env["YT_CLIENT_SECRET"],
                                   "refresh_token": env["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    with http("https://oauth2.googleapis.com/token", body.encode()) as r:
        return json.load(r)["access_token"]


def published_titles(token: str) -> set[str]:
    """عناوين كل الفيديوهات المنشورة في القناة، حتى لا تُنشر حلقة مرتين."""
    auth = {"Authorization": f"Bearer {token}"}
    api = "https://www.googleapis.com/youtube/v3"
    with http(f"{api}/channels?part=contentDetails&mine=true", headers=auth) as r:
        items = json.load(r).get("items", [])
    if not items:
        return set()
    playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    titles, page = set(), ""
    while True:
        q = urllib.parse.urlencode({"part": "snippet", "playlistId": playlist, "maxResults": 50, "pageToken": page})
        with http(f"{api}/playlistItems?{q}", headers=auth) as r:
            data = json.load(r)
        titles |= {i["snippet"]["title"] for i in data.get("items", [])}
        page = data.get("nextPageToken")
        if not page:
            return titles


def upload_video(token: str, video: Path, meta: dict) -> str:
    body = json.dumps({
        "snippet": {"title": meta["title"], "description": meta["description"], "tags": meta["tags"],
                    "categoryId": meta["categoryId"], "defaultLanguage": "ar", "defaultAudioLanguage": "ar"},
        "status": {"privacyStatus": meta["privacy"], "selfDeclaredMadeForKids": False},
    }, ensure_ascii=False).encode()
    size = video.stat().st_size
    with http("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
              body, {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8",
                     "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}) as r:
        location = r.headers["Location"]
    with video.open("rb") as f, http(location, f.read(), {"Content-Type": "video/mp4"}, "PUT") as r:
        return json.load(r)["id"]


def publish(args) -> int:
    series = load_series()
    episodes = [ep for ep in series["episodes"] if not args.episodes or ep["id"] in args.episodes]
    token = youtube_token()
    done = published_titles(token)
    for ep in episodes:
        video = OUTPUT_DIR / f"{ep['id']}.mp4"
        meta = episode_metadata(ep, series)
        if ep.get("approved") is not True:
            log(f"- {ep['id']}: لم تتم الموافقة عليها بعد (approved = true)، لن تُنشر")
        elif not video.exists():
            log(f"- {ep['id']}: لا يوجد فيديو بعد، تخطّيتها")
        elif meta["title"] in done:
            log(f"- {ep['id']}: منشورة سابقاً")
        else:
            vid = upload_video(token, video, meta)
            log(f"✓ نُشرت {ep['id']}: https://youtu.be/{vid}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="توليد حلقات سلسلة ميراي سند")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="تنزيل MoneyPrinterTurbo وتثبيته").set_defaults(func=setup)
    sub.add_parser("list", help="عرض الحلقات").set_defaults(func=list_episodes)
    g = sub.add_parser("generate", help="توليد الحلقات")
    g.add_argument("episodes", nargs="*", help="أسماء الحلقات (الافتراضي: الكل)")
    g.add_argument("--source", choices=["pixabay", "pexels", "coverr", "local"],
                   help="مصدر اللقطات (الافتراضي: أول مصدر له مفتاح، وإلا local)")
    g.add_argument("--voice", help="تجاوز الصوت لكل الحلقات (مثلاً no-voice للتجربة)")
    g.set_defaults(func=generate)
    pb = sub.add_parser("publish", help="نشر الحلقات الجاهزة على قناة يوتيوب")
    pb.add_argument("episodes", nargs="*", help="أسماء الحلقات (الافتراضي: الكل)")
    pb.set_defaults(func=publish)
    args = parser.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
