---
name: map-route
description: "/map-route <from> <to> — animates a stylised 3D city map with a route drawing from A to B, a navigation card (time · distance) and an arrival state, as a 9:16 HTML animation. Use when the user types /map-route or asks for an animated route / مسار على الخريطة."
---

# /map-route — مسار متحرك على خريطة 3D

Input: from / to text, e.g. `/map-route من البيت للدوام`. Invent a plausible time and distance (e.g. 12 دقيقة · 6 كم) unless the user gives them.

## Build
- A tilted isometric city in CSS 3D: a ground plane with `transform: rotateX(55deg) rotateZ(-35deg)`, a street grid, and 30-60 extruded buildings (boxes with a top + 2 visible side faces, varied heights), a few round low-poly trees and a park patch.
- The route = an SVG polyline on the ground plane following the streets (3-5 turns), drawn with `stroke-dashoffset`, with a glowing head dot leading it.
- Start pin (label = from) and end pin (label = to) as floating pills that stay facing the camera.

## Look
- Default dark map: ground `#141417`, streets `#1E1E22`, buildings `#2A2A31` tops / `#1C1C21` sides, dark green trees. Route + head in the accent (lime `#C9FF2F`) with glow. Light mode if asked.
- Top navigation card (frosted glass, radius 28): big "12 دقيقة" + small "6 كم · أسرع طريق" + a direction-arrow chip. On arrival the chip turns into an accent "وصلت ✓".

## Motion (about 5 s)
1. 0.0-0.3 s: the map fades in, camera slightly zoomed on the start pin.
2. 0.3-1.7 s: the route draws and the camera (the plane's translate) follows the head; minutes count down on the card.
3. 1.7-2.1 s: the end pin drops with a bounce, the card switches to "وصلت", the camera eases out to show the whole route.
4. Rest: a light pulse runs along the route on loop.

Follow every rule below.

## Output rules (all es.igner animation commands)
- Produce ONE self-contained HTML file (show it as an artifact, or save it as `map-route-<slug>.html`). No build step, no external images. Allowed external resources: Google Fonts and one GSAP script (`https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js`), or pure CSS/JS.
- Stage = 1080x1920 (9:16) `#stage`, scaled with `transform: scale()` to fit the viewport and centered on a black page, so it can be screen-recorded straight into a Reel.
- Autoplay on load, 4 to 6 seconds, then hold the final frame 2 seconds and loop (restart with a short fade). Add a small "↻" replay button bottom-right.
- All Arabic text `dir="rtl"`. Fonts from Google Fonts (headings: "Cairo" or "Reem Kufi" 800-900, body: "Cairo" / "IBM Plex Sans Arabic"). Always use Western digits 0-9.
- Default look: near-black background `#0E0E10`, off-white text `#F4F3EE`, ONE accent color (default lime `#C9FF2F`). If the user names colors, a mood or a brand, use those instead.
- Motion quality: eased (power3 / expo / back), staggered, nothing linear except counters. The payoff (the moment the picture is complete) must land within the first 2 seconds so it works in a fast Reel.
- Keep everything inside a safe area: 90 px from left/right, 240 px from top, 300 px from bottom.
- The text after the command is the subject. If it is empty, pick a fitting example and say which one.
- After the file, reply with ONE short line: what you made + "اكتب نفس الأمر بموضوع تاني وأنا أعيده".
