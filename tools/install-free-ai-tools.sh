#!/usr/bin/env bash
# تثبيت كل أدوات الفيديو المجانية لمشروع ميراي سند.
# الاستخدام: bash tools/install-free-ai-tools.sh
set -euo pipefail
cd "$(dirname "$0")/.."

command -v ffmpeg >/dev/null || { echo "ثبّت ffmpeg أولاً: sudo apt install ffmpeg"; exit 1; }
command -v uv >/dev/null || python3 -m pip install --user uv

# 1) MoneyPrinterTurbo (المحرك الأساسي للسلسلة)
python3 mirai.py setup

# 2) أدوات الذكاء الاصطناعي في بيئة منفصلة .venv
uv venv .venv --python 3.13 --allow-existing
uv pip install --python .venv/bin/python -r requirements-ai-tools.txt

# 3) صوت عربي محلي لـ Piper (حوالي 60 ميغابايت)
mkdir -p vendor/piper
.venv/bin/python -m piper.download_voices --data-dir vendor/piper ar_JO-kareem-medium

# 4) خادم MCP لتحرير الفيديو (مُعرّف في .mcp.json ويعمل تلقائياً في Claude Code)
uvx mcp-video --help >/dev/null && echo "mcp-video جاهز"

echo "تم. اقرأ docs/free-ai-tools.md لطريقة الاستخدام."
