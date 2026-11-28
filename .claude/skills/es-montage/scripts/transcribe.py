"""Word-timed transcript of the prepared video → <work>/words.json (source time).

Uses openai-whisper, or faster-whisper if that is what is installed.

usage: transcribe.py WORK_DIR [--language ar] [--model small] [--prompt "Claude, Remotion"]
"""
import sys
import argparse
import importlib.util
import json
from pathlib import Path

# Windows consoles default to a legacy codepage
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def with_openai_whisper(path, model_name, language, prompt):
    import torch
    import whisper
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_name, device=device)
    # fp16 gives NaNs on some older GPUs; fp32 is always safe
    res = model.transcribe(str(path), language=language, word_timestamps=True,
                           initial_prompt=prompt or None, fp16=False)
    for seg in res["segments"]:
        for w in seg.get("words", []):
            yield w["word"], w["start"], w["end"]


def with_faster_whisper(path, model_name, language, prompt):
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="auto", compute_type="int8")
    segments, _ = model.transcribe(str(path), language=language, word_timestamps=True,
                                   initial_prompt=prompt or None, vad_filter=True)
    for seg in segments:
        for w in seg.words or []:
            yield w.word, w.start, w.end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work")
    ap.add_argument("--language", default="ar")
    ap.add_argument("--model", default="small", help="tiny / base / small / medium / turbo")
    ap.add_argument("--prompt", default="", help="names Whisper should spell right, e.g. \"Claude, Remotion\"")
    a = ap.parse_args()

    work = Path(a.work)
    src = work / "source.mp4"
    if not src.exists():
        raise SystemExit("source.mp4 not found - run cut_silences.py first")

    engine = with_openai_whisper if importlib.util.find_spec("whisper") else with_faster_whisper
    print(f"transcribing with {engine.__name__[5:]} ({a.model})... this can take a few minutes")
    words = []
    for text, start, end in engine(src, a.model, a.language, a.prompt):
        text = text.strip()
        if text:
            words.append({"text": text, "start": round(float(start), 3), "end": round(float(end), 3)})

    (work / "words.json").write_text(json.dumps({"language": a.language, "words": words},
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(words)} words -> {work / 'words.json'}")
    print("check the spelling of names in words.json (edit only \"text\"), then run build_props.py")


if __name__ == "__main__":
    main()
