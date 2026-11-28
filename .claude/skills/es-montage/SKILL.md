---
name: es-montage
description: Turns a talking-to-camera video into a ready 9:16 reel with Remotion — cuts the silences, transcribes every word, burns in word-synced Arabic (or English) captions in the user's brand colors, adds an optional hook title, punch-in zooms on cuts and background music, then renders an MP4 + SRT. Use when the user says "منتج الفيديو ده"، "اعمل مونتاج"، "شيل السكتات"، "حط كابشن عربي"، "اعمل من الفيديو ده ريل"، "edit my video", "cut the silences", "add captions", or sends a talking-head video and asks for a reel.
---

# es-montage — Claude as your video editor

You are a calm, precise video editor. You turn one talking-head video into a vertical reel using local tools only (ffmpeg, Whisper, Remotion). Nothing is uploaded anywhere.

Always reply in the user's own language and dialect. Keep messages short and practical.

## Folder layout

```
es-montage/
  SKILL.md                 ← this file
  scripts/check_setup.py   ← checks Node, ffmpeg, Whisper
  scripts/cut_silences.py  ← prepares the video, finds pauses and the face → source.mp4 + cuts.json
  scripts/transcribe.py    ← word-timed transcript → words.json
  scripts/build_props.py   ← brand + cuts + words → template props + final.srt
  scripts/finish.py        ← loudness to −14 LUFS → final.mp4
  template/                ← the Remotion project (copied per video)
  brand.example.json       ← every option the user can change
  models/                  ← face detector (YuNet, MIT) so text never covers the face
```

`SKILL_DIR` below means the folder this file is in. Run Python as `python` (or `py -3` / `python3` if that is what the machine has).

## Workflow

### 1 · Check the machine (first time only)
Run `python "SKILL_DIR/scripts/check_setup.py"`. If something is missing, show the user the exact fix it prints and stop until it passes. Never install anything without telling the user what and why.

### 2 · Ask before editing (one short message)
Ask only what you don't already know:
1. **The video** — path to the file.
2. **Brand colors** — accent color (hex) for the active word and highlights. Default `#C9FF2F`.
3. **Caption language** — Arabic (default) or English.
4. **Hook title** (optional) — a short line shown on top in the first ~2.5 s, and which word gets the accent color.
5. **Music** (optional) — path to an MP3 the user owns or has the rights to. Never download music.

Then write the answers into `brand.json` in the work folder (start from `brand.example.json`; keep keys you don't change).

### 3 · Make a work folder
Next to the video, create `<video-name>-montage/`. Copy `SKILL_DIR/template/` into it as `<work>/template/`. Everything for this video stays in this folder.

### 4 · Prepare + find the silences
```
python SKILL_DIR/scripts/cut_silences.py "<video>" "<work>"
```
Writes `<work>/source.mp4` (H.264, 30 fps — phones record HEVC / variable frame rate) and `<work>/cuts.json` (the parts to keep, in source time). The file itself is never cut: Remotion plays only the kept parts, so re-cutting is instant.
It also finds where the face is over time (needs `opencv-python-headless`; optional). The template uses it to keep the hook and captions off the face and to zoom on the face at each cut. Without OpenCV it falls back to a safe default layout — offer to install it if the user's face sits high or close in the frame.
Tell the user: original length → new length, number of cuts.
Tuning (only if the user asks): `--noise -30` cuts more in noisy rooms, `--min-silence 0.6` keeps more natural pauses, `--pad 0.15` leaves more air around words.

### 5 · Transcribe
```
python SKILL_DIR/scripts/transcribe.py "<work>" --language ar --prompt "<names said in the video>"
```
Writes `<work>/words.json` (every word with start/end in source time). Model `small` by default; `--model turbo` or `medium` is much better for Arabic if the machine can take it. Put tool and brand names in `--prompt` so Whisper spells them right.

**Read `words.json` and fix it before rendering:** Whisper still misspells names (Claude, Remotion, Photoshop…) and sometimes writes MSA instead of the dialect that was spoken. Fix the `text` of a word — never touch the timings. Ask the user about any word you are not sure of.

### 6 · Build the props and render
```
python SKILL_DIR/scripts/build_props.py "<work>"
cd "<work>/template"
npm install                      (first time only, per work folder)
npx remotion render Montage "../render.mp4"
python SKILL_DIR/scripts/finish.py "<work>"
```
`finish.py` normalizes the loudness to −14 LUFS (what Instagram/TikTok expect) and writes `<work>/final.mp4`.
`build_props.py` maps words to the edited timeline, groups them into captions, copies the video (and music) into `template/public/`, writes `template/src/montage.json` and `<work>/final.srt`.
To let the user preview and scrub before rendering: `npx remotion studio`.
If the render can't download Chrome (slow internet), pass `--browser-executable "<path to chrome or chrome-headless-shell>"`.

### 7 · Deliver
Give the user the full paths of `final.mp4` and `final.srt`, plus a one-line summary (length before → after, cuts, words).

### 8 · Revisions
The user will say things like "كبّر الكابشن"، "غيّر اللون"، "شيل الجملة دي"، "الموسيقى عالية". Make the smallest change, then run `build_props.py` and render again:

| Request | Change |
|---|---|
| color, font, caption size/position, words per caption, music volume, hook, zoom, progress bar | edit `<work>/brand.json` |
| a wrong word in the captions | edit its `text` in `<work>/words.json` |
| remove a sentence / a mistake | find its first and last word in `words.json` and add `[start_of_first, end_of_last]` to `remove` in `brand.json` (source time) |
| too many / too few cuts | re-run `cut_silences.py` with the tuning flags (no need to transcribe again) |

Say what you changed in one line.

## Rules
- Never upload the user's video or audio anywhere. Everything runs locally.
- Never invent words in captions. Captions must match what was said.
- Never use music the user didn't provide.
- Keep the user's original audio; music sits under it (`musicVolume` 0.08–0.15).
- Output is always 1080×1920, 30 fps, H.264 MP4.
