"""Prepare the video and find the parts worth keeping.

1. Makes <work>/source.mp4: H.264, constant 30 fps, at least 1080x1920 coverage
   (phones record HEVC / variable frame rate; this keeps every later step exact).
2. Detects silences with ffmpeg and writes <work>/cuts.json with the segments to keep,
   in source time. Nothing is cut from the file itself — Remotion plays only the kept parts.

usage: cut_silences.py VIDEO WORK_DIR [--noise -35] [--min-silence 0.45] [--pad 0.12]
"""
import sys
import argparse
import json
import re
import subprocess
from pathlib import Path

# Windows consoles default to a legacy codepage
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def probe_duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=nw=1:nk=1", str(path)])
    return float(out.stdout.strip())


def make_proxy(src, dst):
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
        return
    # scale so the frame covers 1080x1920 (the template crops the rest)
    vf = ("scale='if(gt(a,1080/1920),-2,1080)':'if(gt(a,1080/1920),1920,-2)',"
          "fps=30,format=yuv420p")
    res = run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", vf,
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
               "-movflags", "+faststart", str(dst)])
    if res.returncode != 0:
        raise SystemExit(f"ffmpeg failed while preparing the video:\n{res.stderr}")


def probe_size(path):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
               "-of", "csv=p=0", str(path)])
    w, h = out.stdout.strip().split(",")[:2]
    return int(w), int(h)


def detect_faces(path):
    """Where the head is over time (fractions of the frame), so text never sits on it.
    Optional: needs opencv (pip install opencv-python-headless). Returns [] without it."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return []
    model = Path(__file__).resolve().parent.parent / "models" / "face_detection_yunet_2023mar.onnx"
    try:
        if hasattr(cv2, "FaceDetectorYN") and model.exists():
            # loaded from memory: opencv can't open non-ASCII paths on Windows
            yunet = cv2.FaceDetectorYN.create("onnx", np.frombuffer(model.read_bytes(), np.uint8),
                                              np.zeros(0, np.uint8), (320, 320), 0.7)
            def find(img):
                yunet.setInputSize((img.shape[1], img.shape[0]))
                _, faces = yunet.detect(img)
                return [] if faces is None else [tuple(float(v) for v in f[:4]) for f in faces]
        elif hasattr(cv2, "CascadeClassifier"):  # older opencv
            haar = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            def find(img):
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                return [tuple(float(v) for v in f) for f in haar.detectMultiScale(gray, 1.1, 6, minSize=(40, 40))]
        else:
            return []

        # frames come through ffmpeg (same unicode-path reason), downscaled to ~640px
        w, h = probe_size(path)
        k = 640 / max(w, h)
        sw, sh = int(w * k) // 2 * 2, int(h * k) // 2 * 2
        duration = probe_duration(path)
        rate = min(2.0, 240 / max(0.1, duration))  # 2 per second, at most 240 frames
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={rate},scale={sw}:{sh}",
                              "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
        frames = np.frombuffer(raw, np.uint8)[: len(raw) // (sw * sh * 3) * sw * sh * 3].reshape(-1, sh, sw, 3)
        boxes = []
        for i, img in enumerate(frames):
            img = np.ascontiguousarray(img)
            faces = find(img)
            if faces:
                x, y, bw, bh = max(faces, key=lambda f: f[2] * f[3])
                # detectors box brows to chin; grow it to cover hair and beard
                boxes.append({"t": round(i / rate, 2),
                              "x0": round(max(0, (x - 0.15 * bw) / sw), 3), "y0": round(max(0, (y - 0.45 * bh) / sh), 3),
                              "x1": round(min(1, (x + 1.15 * bw) / sw), 3), "y1": round(min(1, (y + 1.15 * bh) / sh), 3)})
    except Exception as e:  # face position is a nice-to-have, never a blocker
        print(f"face detection skipped: {e}")
        return []
    return boxes


def detect_silences(path, noise, min_silence):
    res = run(["ffmpeg", "-v", "info", "-i", str(path), "-af",
               f"silencedetect=noise={noise}dB:d={min_silence}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", res.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", res.stderr)]
    return list(zip(starts, ends + [None] * (len(starts) - len(ends))))


def keep_segments(silences, duration, pad, min_keep=0.25):
    keep, cursor = [], 0.0
    for s, e in silences:
        e = duration if e is None else e
        seg_end = min(duration, max(0.0, s) + pad)
        if seg_end - cursor >= min_keep:
            keep.append([round(cursor, 3), round(seg_end, 3)])
        cursor = max(cursor, e - pad)
    if duration - cursor >= min_keep:
        keep.append([round(cursor, 3), round(duration, 3)])
    # merge overlaps created by the padding
    merged = []
    for seg in keep:
        if merged and seg[0] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], seg[1])
        else:
            merged.append(seg)
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("work")
    ap.add_argument("--noise", type=float, default=-35, help="silence threshold in dB (higher = cuts more)")
    ap.add_argument("--min-silence", type=float, default=0.45, help="shortest pause to remove, seconds")
    ap.add_argument("--pad", type=float, default=0.12, help="air kept before/after each phrase, seconds")
    a = ap.parse_args()

    src, work = Path(a.video), Path(a.work)
    work.mkdir(parents=True, exist_ok=True)
    proxy = work / "source.mp4"
    print("preparing video...")
    make_proxy(src, proxy)

    duration = probe_duration(proxy)
    silences = detect_silences(proxy, a.noise, a.min_silence)
    keep = keep_segments(silences, duration, a.pad)
    kept = sum(e - s for s, e in keep)
    faces = detect_faces(proxy)

    (work / "cuts.json").write_text(json.dumps({
        "source": "source.mp4",
        "duration": round(duration, 3),
        "size": list(probe_size(proxy)),
        "faces": faces,
        "settings": {"noise": a.noise, "min_silence": a.min_silence, "pad": a.pad},
        "keep": keep,
    }, indent=2), encoding="utf-8")

    print(f"original {duration:.1f}s -> {kept:.1f}s  ({len(keep)} parts, {max(0, len(keep) - 1)} cuts)")
    print(f"face found in {len(faces)} frames - text will stay clear of it" if faces else
          "no face position (opencv missing or no clear face) - using safe default layout")
    print(f"wrote {work / 'cuts.json'}")


if __name__ == "__main__":
    main()
