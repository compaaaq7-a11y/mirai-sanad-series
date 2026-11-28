"""Check that the machine has everything es-montage needs."""
import importlib.util
import platform
import re
import shutil
import subprocess
import sys

WIN = platform.system() == "Windows"
MAC = platform.system() == "Darwin"

# Windows consoles default to a legacy codepage
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def version_of(cmd):
    exe = shutil.which(cmd)
    if not exe:
        return None
    try:
        out = subprocess.run([exe, "--version" if cmd != "ffmpeg" else "-version"],
                             capture_output=True, text=True, timeout=30)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception:
        return "?"


def fix(win, mac, linux):
    return win if WIN else mac if MAC else linux


checks = []

node = version_of("node")
node_ok = False
if node:
    m = re.search(r"v(\d+)", node)
    node_ok = bool(m) and int(m.group(1)) >= 18
checks.append(("Node.js 18+", node_ok, node or "not found",
               fix("winget install OpenJS.NodeJS.LTS", "brew install node",
                   "install Node 18+ from https://nodejs.org")))

npx_ok = shutil.which("npx") is not None
checks.append(("npx", npx_ok, "found" if npx_ok else "not found", "comes with Node.js — reinstall Node"))

for tool in ("ffmpeg", "ffprobe"):
    v = version_of(tool) if tool == "ffmpeg" else ("found" if shutil.which(tool) else None)
    checks.append((tool, v is not None, v or "not found",
                   fix("winget install Gyan.FFmpeg  (then open a new terminal)",
                       "brew install ffmpeg", "sudo apt install ffmpeg")))

py_ok = sys.version_info >= (3, 9)
checks.append(("Python 3.9+", py_ok, sys.version.split()[0], "install Python 3.10–3.12 from https://python.org"))

has_whisper = importlib.util.find_spec("whisper") is not None
has_faster = importlib.util.find_spec("faster_whisper") is not None
checks.append(("Whisper (speech to text)", has_whisper or has_faster,
               "openai-whisper" if has_whisper else "faster-whisper" if has_faster else "not found",
               f'"{sys.executable}" -m pip install -U openai-whisper   (Python 3.10–3.12 recommended)'))

# optional: face position, so captions and the hook never cover the face
has_cv = importlib.util.find_spec("cv2") is not None

all_ok = True
for name, ok, info, how in checks:
    print(f"[{'OK ' if ok else 'MISSING'}] {name}: {info}")
    if not ok:
        all_ok = False
        print(f"          fix: {how}")

print(f"[{'OK ' if has_cv else 'OPTIONAL'}] OpenCV (keeps text off the face): "
      f"{'found' if has_cv else 'not found'}")
if not has_cv:
    print(f'          add it with: "{sys.executable}" -m pip install opencv-python-headless')

print()
print("READY" if all_ok else "NOT READY - fix the missing items above, then run this again.")
sys.exit(0 if all_ok else 1)
