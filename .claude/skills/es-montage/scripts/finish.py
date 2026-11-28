"""Last step: bring the rendered reel to social-media loudness.

Takes <work>/render.mp4, normalizes the audio to -14 LUFS (true peak -1.5 dB),
copies the video stream untouched, and writes <work>/final.mp4.

usage: finish.py WORK_DIR [--lufs -14]
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Windows consoles default to a legacy codepage
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--lufs", type=float, default=-14)
    a = ap.parse_args()

    work = Path(a.work)
    src, dst = work / "render.mp4", work / "final.mp4"
    if not src.exists():
        raise SystemExit("render.mp4 not found - render with Remotion first")

    target = f"loudnorm=I={a.lufs}:TP=-1.5:LRA=11"
    # pass 1: measure
    res = run(["ffmpeg", "-hide_banner", "-i", str(src), "-af", target + ":print_format=json",
               "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr)
    if not m:
        raise SystemExit(f"could not measure loudness:\n{res.stderr[-800:]}")
    st = json.loads(m.group(0))
    # pass 2: apply with the measured values (more accurate than one pass)
    af = (f"{target}:measured_I={st['input_i']}:measured_TP={st['input_tp']}"
          f":measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}"
          f":offset={st['target_offset']}:linear=true")
    res = run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c:v", "copy", "-af", af,
               "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)])
    if res.returncode != 0:
        raise SystemExit(f"ffmpeg failed:\n{res.stderr}")
    print(f"loudness {float(st['input_i']):.1f} -> {a.lufs:.0f} LUFS")
    print(f"done: {dst}")


if __name__ == "__main__":
    main()
