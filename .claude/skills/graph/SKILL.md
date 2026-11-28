---
name: graph
description: "/graph <from> <to> — animates a growth chart: a big counter counting up while a curve draws and milestones pop, as a 9:16 HTML animation (followers, sales, views…). Use when the user types /graph or asks for an animated growth chart / عدّاد / رسم بياني متحرك."
---

# /graph — عدّاد + منحنى نمو

Input: start, end and optionally the metric, e.g. `/graph من 0 لـ 100 ألف`. Default metric = المتابعين.

## Look
- Dark background with a soft accent glow behind a large frosted-glass card (radius 48, 1 px light border, a specular highlight on the top edge).
- Top-right: the metric label (small, grey). Below it a HUGE counter (monospace digits, e.g. "JetBrains Mono" 800 at about 190 px, tabular numbers) with Western digits and thousands separators.
- Chart: x-axis of 9 months (يناير … سبتمبر), faint grid, an exponential curve in the accent with a gradient area fill under it, 2 milestone dots with small labels (e.g. "10 آلاف", "50 ألف"). The end dot is a pulsing ring with a pill "100 ألف متابع".

## Motion (about 4.5 s)
1. 0.0-0.3 s: the card rises in.
2. 0.3-1.8 s: the curve draws left to right (slow first, then shooting up) and the counter counts in sync with the curve height (ease expo.in); milestones pop as the head passes them.
3. 1.8 s: the final number lands and turns accent, the end ring pulses, the pill pops (back.out).
4. Rest: the ring keeps pulsing, a tiny shimmer passes over the number.

Follow every rule below.

## Output rules (all es.igner animation commands)
- Produce ONE self-contained HTML file (show it as an artifact, or save it as `graph-<slug>.html`). No build step, no external images. Allowed external resources: Google Fonts and one GSAP script (`https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js`), or pure CSS/JS.
- Stage = 1080x1920 (9:16) `#stage`, scaled with `transform: scale()` to fit the viewport and centered on a black page, so it can be screen-recorded straight into a Reel.
- Autoplay on load, 4 to 6 seconds, then hold the final frame 2 seconds and loop (restart with a short fade). Add a small "↻" replay button bottom-right.
- All Arabic text `dir="rtl"`. Fonts from Google Fonts (headings: "Cairo" or "Reem Kufi" 800-900, body: "Cairo" / "IBM Plex Sans Arabic"). Always use Western digits 0-9.
- Default look: near-black background `#0E0E10`, off-white text `#F4F3EE`, ONE accent color (default lime `#C9FF2F`). If the user names colors, a mood or a brand, use those instead.
- Motion quality: eased (power3 / expo / back), staggered, nothing linear except counters. The payoff (the moment the picture is complete) must land within the first 2 seconds so it works in a fast Reel.
- Keep everything inside a safe area: 90 px from left/right, 240 px from top, 300 px from bottom.
- The text after the command is the subject. If it is empty, pick a fitting example and say which one.
- After the file, reply with ONE short line: what you made + "اكتب نفس الأمر بموضوع تاني وأنا أعيده".
