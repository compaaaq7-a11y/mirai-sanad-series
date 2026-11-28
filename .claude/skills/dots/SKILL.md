---
name: dots
description: "/dots <subject> — builds an image out of thousands of dots that fly in and assemble into a silhouette scene (halftone / dot-matrix art) as a 9:16 HTML canvas animation. Use when the user types /dots or asks for a dots / particles / halftone picture of something."
---

# /dots — صورة من آلاف النقط

Input: a subject (e.g. `/dots جمل بالصحرا`, `/dots صقر`).

## Build
- Design the scene as a bold silhouette composition on an offscreen canvas: a big circle (sun or moon) behind the subject's silhouette, and 3-4 horizontal bands at the bottom (dunes / ground). Draw the silhouette with canvas paths, or a fitting emoji glyph scaled up and filled solid. What matters is a crisp, recognizable outline.
- Sample the offscreen canvas on a grid (every 14-16 px). Each sample becomes a dot: inside the circle but outside the subject = bright dot; the subject = empty (negative space); the bands = dots in a second shade. Vary the dot radius slightly with brightness (halftone feel). Count the dots.

## Look
- Background `#0B0B0C`. Dots in the accent (default lime `#C9FF2F` for the disc, a darker shade for the bands). If the user asks for a sunset, use orange → red.
- Title at the top: the subject (Cairo 900, about 96 px) + subtitle "من N نقطة" (N = the real dot count, Western digits).

## Motion (about 4.5 s), canvas + requestAnimationFrame
1. 0.0 s: dots start scattered randomly across the stage (and a little outside it), faint.
2. 0.2-1.7 s: every dot flies to its target, delayed by its distance from the center (easeOutExpo), brightening as it lands.
3. 1.7 s: the picture is complete, a ripple of brightness passes through the dots, the counter finishes.
4. Rest: the dots twinkle subtly; the subject never moves.

Follow every rule below.

## Output rules (all es.igner animation commands)
- Produce ONE self-contained HTML file (show it as an artifact, or save it as `dots-<slug>.html`). No build step, no external images. Allowed external resources: Google Fonts and one GSAP script (`https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js`), or pure CSS/JS.
- Stage = 1080x1920 (9:16) `#stage`, scaled with `transform: scale()` to fit the viewport and centered on a black page, so it can be screen-recorded straight into a Reel.
- Autoplay on load, 4 to 6 seconds, then hold the final frame 2 seconds and loop (restart with a short fade). Add a small "↻" replay button bottom-right.
- All Arabic text `dir="rtl"`. Fonts from Google Fonts (headings: "Cairo" or "Reem Kufi" 800-900, body: "Cairo" / "IBM Plex Sans Arabic"). Always use Western digits 0-9.
- Default look: near-black background `#0E0E10`, off-white text `#F4F3EE`, ONE accent color (default lime `#C9FF2F`). If the user names colors, a mood or a brand, use those instead.
- Motion quality: eased (power3 / expo / back), staggered, nothing linear except counters. The payoff (the moment the picture is complete) must land within the first 2 seconds so it works in a fast Reel.
- Keep everything inside a safe area: 90 px from left/right, 240 px from top, 300 px from bottom.
- The text after the command is the subject. If it is empty, pick a fitting example and say which one.
- After the file, reply with ONE short line: what you made + "اكتب نفس الأمر بموضوع تاني وأنا أعيده".
