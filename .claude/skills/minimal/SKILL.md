---
name: minimal
description: "/minimal <idea> — turns a short idea into a clean black-and-white minimal motion piece (outline shapes + one accent) as a 9:16 HTML animation, e.g. a ball climbing bars for خطوة خطوة. Use when the user types /minimal or asks for a minimal / مينيمال motion graphic of an idea."
---

# /minimal — فكرة في موشن مينيمال

Input: a short idea or phrase (e.g. `/minimal خطوة خطوة`). Translate it into ONE simple visual metaphor made of basic shapes (lines, bars, circles). Examples: progress → a ball climbing ascending outline bars; focus → circles shrinking to one dot; balance → a seesaw settling; growth → a line branching into a tree of lines.

## Look
- Pure black `#000` background. Shapes = 3 px white outlines only, no fills. ONE accent (default lime `#C9FF2F`) used only for the moving hero element and the last word of the title.
- Title at the top in heavy Arabic sans (Cairo 900, about 90 px): the phrase in white, then a finishing word appears in the accent (e.g. "خطوة خطوة" + "لفوق").
- A thin baseline across the bottom third.

## Motion (about 4 s), example for خطوة خطوة
1. 0.0-0.5 s: 6 outline bars grow from the baseline (stagger), heights ascending right-to-left.
2. 0.3-1.8 s: the accent ball bounces from bar to bar upward (arc path, squash on landing, an elliptical ripple ring at each landing); title words pop in with the bounces.
3. 1.8 s: the ball lands on the tallest bar, the accent word appears, a bigger ripple.
4. Rest: the ball idles with a tiny bounce, the ripple loops softly.

Follow every rule below.

## Output rules (all es.igner animation commands)
- Produce ONE self-contained HTML file (show it as an artifact, or save it as `minimal-<slug>.html`). No build step, no external images. Allowed external resources: Google Fonts and one GSAP script (`https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js`), or pure CSS/JS.
- Stage = 1080x1920 (9:16) `#stage`, scaled with `transform: scale()` to fit the viewport and centered on a black page, so it can be screen-recorded straight into a Reel.
- Autoplay on load, 4 to 6 seconds, then hold the final frame 2 seconds and loop (restart with a short fade). Add a small "↻" replay button bottom-right.
- All Arabic text `dir="rtl"`. Fonts from Google Fonts (headings: "Cairo" or "Reem Kufi" 800-900, body: "Cairo" / "IBM Plex Sans Arabic"). Always use Western digits 0-9.
- Default look: near-black background `#0E0E10`, off-white text `#F4F3EE`, ONE accent color (default lime `#C9FF2F`). If the user names colors, a mood or a brand, use those instead.
- Motion quality: eased (power3 / expo / back), staggered, nothing linear except counters. The payoff (the moment the picture is complete) must land within the first 2 seconds so it works in a fast Reel.
- Keep everything inside a safe area: 90 px from left/right, 240 px from top, 300 px from bottom.
- The text after the command is the subject. If it is empty, pick a fitting example and say which one.
- After the file, reply with ONE short line: what you made + "اكتب نفس الأمر بموضوع تاني وأنا أعيده".
