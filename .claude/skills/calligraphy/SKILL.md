---
name: calligraphy
description: "/calligraphy <phrase> — animates an Arabic phrase as luxury calligraphy that writes itself stroke by stroke (metallic ink, glowing pen-light, particles) as a 9:16 HTML animation. Use when the user types /calligraphy or asks for animated Arabic calligraphy / خط عربي متحرك."
---

# /calligraphy — خط عربي بيكتب نفسه

Input: the Arabic phrase after the command (e.g. `/calligraphy حيّاك الله`). Optional style word: رقعة · ديواني · ثلث · كوفي (default رقعة).

## Look
- Background: deep warm black (`#0E0B07`, radial glow `#1A130A` behind the text), slow drifting dust / bokeh particles (30-60 small blurred dots, low opacity).
- Phrase in a calligraphic Google Font: رقعة → "Aref Ruqaa" 700, ثلث/ديواني → "Amiri" 700, كوفي → "Reem Kufi" 700. Size it to fill about 80% of the width.
- Ink = metallic gold gradient (`#7A5418 → #F7D27A → #B8862F`, 120°) with a soft outer glow. If the user gives an accent color, blend it into the highlight.
- Under the phrase: a thin gold rule with a small diamond in the middle, and the style name in small text (e.g. "خط الرقعة").

## Motion (about 4 s)
1. 0.0-1.6 s: the phrase draws itself. Use SVG `<text>` with `stroke-dasharray / stroke-dashoffset` animating the outline right-to-left, while a glowing pen-light dot travels along the writing direction.
2. 1.2-1.9 s: the gold fill fades in under the outline and a specular shine sweeps across once.
3. 1.8-2.3 s: the rule draws out from the center, the diamond pops, the style label fades up.
4. Rest: gentle float (±6 px), particles drift, the glow breathes.

Follow every rule in the "Output rules" section below.

## Output rules
- Produce ONE self-contained HTML file (show it as an artifact, or save it as `calligraphy-<slug>.html`). No build step, no external images. Allowed external resources: Google Fonts and one GSAP script (`https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js`), or pure CSS/JS.
- Stage = 1080x1920 (9:16) `#stage`, scaled with `transform: scale()` to fit the viewport and centered on a black page, so it can be screen-recorded straight into a Reel.
- Autoplay on load, 4 to 6 seconds, then hold the final frame 2 seconds and loop (restart with a short fade). Add a small "↻" replay button bottom-right.
- All Arabic text `dir="rtl"`. Always use Western digits 0-9.
- Motion quality: eased (power3 / expo / back), staggered. The payoff must land within the first 2 seconds.
- Keep everything inside a safe area: 90 px from left/right, 240 px from top, 300 px from bottom.
- If no phrase is given, use "بسم الله" and say so.
- After the file, reply with ONE short line: what you made + "اكتب نفس الأمر بموضوع تاني وأنا أعيده".
