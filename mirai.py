#!/usr/bin/env python3
"""سلسلة ميراي سند: توليد حلقات الفيديو بأداة MoneyPrinterTurbo.

الاستخدام:
    python3 mirai.py setup                 # تنزيل الأداة وتثبيتها (مرة واحدة)
    python3 mirai.py list                  # عرض الحلقات
    python3 mirai.py generate              # توليد كل الحلقات
    python3 mirai.py generate ep01-intro   # توليد حلقة واحدة أو أكثر
    python3 mirai.py generate --source local   # استخدام لقطات من مجلد assets/

متغيرات البيئة الاختيارية:
    PEXELS_API_KEY  مفتاح Pexels المجاني للقطات الفيديو (بدونه تُستخدم assets/)
    MPT_DIR         مكان MoneyPrinterTurbo (الافتراضي vendor/MoneyPrinterTurbo)
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


def write_config() -> None:
    """أنشئ config.toml للأداة وضع فيه مفتاح Pexels إن وُجد."""
    config = MPT_DIR / "config.toml"
    if not config.exists():
        shutil.copy2(MPT_DIR / "config.example.toml", config)
    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if key:
        text = config.read_text(encoding="utf-8")
        text = re.sub(r"(?m)^pexels_api_keys\s*=.*$", f"pexels_api_keys = {json.dumps([key])}", text, count=1)
        config.write_text(text, encoding="utf-8")
        log("أُضيف مفتاح Pexels إلى الإعدادات")


def pexels_configured() -> bool:
    if os.environ.get("PEXELS_API_KEY", "").strip():
        return True
    config = MPT_DIR / "config.toml"
    if not config.exists():
        return False
    data = tomllib.loads(config.read_text(encoding="utf-8"))
    return bool(data.get("app", {}).get("pexels_api_keys"))


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
        task.update({k: v for k, v in ep.items() if k not in {"id", "title", "script", "terms"}})
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

    source = args.source or ("pexels" if pexels_configured() else "local")
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
            log(f"✓ {name} → {dest.relative_to(ROOT)}")
        else:
            failed += 1
            log(f"✗ {name}: فشل في مرحلة {task.get('failed_stage')}: {task.get('error')}")
    log(f"النتيجة: {summary.get('succeeded', 0)} نجحت، {failed} فشلت")
    return 1 if failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="توليد حلقات سلسلة ميراي سند")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="تنزيل MoneyPrinterTurbo وتثبيته").set_defaults(func=setup)
    sub.add_parser("list", help="عرض الحلقات").set_defaults(func=list_episodes)
    g = sub.add_parser("generate", help="توليد الحلقات")
    g.add_argument("episodes", nargs="*", help="أسماء الحلقات (الافتراضي: الكل)")
    g.add_argument("--source", choices=["pexels", "pixabay", "local"],
                   help="مصدر اللقطات (الافتراضي: pexels إن وُجد مفتاح، وإلا local)")
    g.add_argument("--voice", help="تجاوز الصوت لكل الحلقات (مثلاً no-voice للتجربة)")
    g.set_defaults(func=generate)
    args = parser.parse_args()
    sys.exit(args.func(args) or 0)


if __name__ == "__main__":
    main()
