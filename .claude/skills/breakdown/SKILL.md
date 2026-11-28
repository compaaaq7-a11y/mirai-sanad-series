---
name: breakdown
description: "/breakdown <object> — draws an object and explodes it into its numbered parts with callout labels (exploded view / منظر مفكّك) as a 9:16 HTML animation. Use when the user types /breakdown or asks to show the parts of a product or object."
---

# /breakdown — منظر مفكّك لأي حاجة

Input: an object (e.g. `/breakdown مبخرة`, `/breakdown دلة قهوة`, `/breakdown سماعة`).

## Build
- Decide 4-6 real parts of the object, top to bottom. For each: an Arabic name (1 word) + a short smart detail (2-4 words), e.g. "الغطاء — نحاس مخرّم".
- Draw the object yourself in inline SVG, built from the parts (each part its own `<g>`), with real material gradients (brass, gold, wood, glass, plastic…), highlights and a soft floor shadow. Stylised 3D look, not flat icons.

## Look
- Dark background (`#0E0E10` with a subtle radial spotlight behind the object).
- Title at the top: the object name (Cairo 900, about 96 px) + subtitle "منظر مفكّك · N قطع" in the accent color.
- Callouts on the right: a thin 1.5 px line from each part to its label. Label = accent number "01" + bold name + small grey detail, on a frosted-glass pill.

## Motion (about 4.5 s)
1. 0.0-0.4 s: the assembled object rises in with the title.
2. 0.4-1.2 s: the parts separate vertically (stagger, expo.out), each slightly rotated, then settles.
3. 0.8-1.9 s: callout lines draw out one by one, labels slide in.
4. Rest: parts float independently (±8 px, different phases). Add smoke or steam wisps if it fits the object.

Follow every rule below.

## Output rules (all es.igner animation commands)
- Produce ONE self-contained HTML file (show it as an artifact, or save it as `breakdown-<slug>.html`). No build step, no external images. Allowed external resources: Google Fonts and one GSAP script (`https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js`), or pure CSS/JS.
- Stage = 1080x1920 (9:16) `#stage`, scaled with `transform: scale()` to fit the viewport and centered on a black page, so it can be screen-recorded straight into a Reel.
- Autoplay on load, 4 to 6 seconds, then hold the final frame 2 seconds and loop (restart with a short fade). Add a small "↻" replay button bottom-right.
- All Arabic text `dir="rtl"`. Fonts from Google Fonts (headings: "Cairo" or "Reem Kufi" 800-900, body: "Cairo" / "IBM Plex Sans Arabic"). Always use Western digits 0-9.
- Default look: near-black background `#0E0E10`, off-white text `#F4F3EE`, ONE accent color (default lime `#C9FF2F`). If the user names colors, a mood or a brand, use those instead.
- Motion quality: eased (power3 / expo / back), staggered, nothing linear except counters. The payoff (the moment the picture is complete) must land within the first 2 seconds so it works in a fast Reel.
- Keep everything inside a safe area: 90 px from left/right, 240 px from top, 300 px from bottom.
- The text after the command is the subject. If it is empty, pick a fitting example and say which one.
- After the file, reply with ONE short line: what you made + "اكتب نفس الأمر بموضوع تاني وأنا أعيده".
