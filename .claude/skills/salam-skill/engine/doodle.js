/* salam-skill — محرك الرسوم الكرتونية المرسومة باليد (Doodle Cartoon)
   شخصية عصوية برأس كبير وتعابير مبالغ فيها، رسومات تُرسم خطاً خطاً، فقاعات تفكير وكلام، واهتزاز خط (line boil).
   كل شيء حتمي بالزمن t (لا CSS animations) حتى يعمل الرندر فريماً فريماً.
   الاستخدام من salam.html:  R.dd = Doodle.build(scene, camLayer, index);  Doodle.draw(R.dd, t, scene);  */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const eob = p => { const c1 = 1.7, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
  const eoc = p => 1 - Math.pow(1 - p, 3);
  const INK = { pencil: '#4a4a4a', blue: '#1f3fae', black: '#1b1b1b', chalk: '#f3f0e6' };
  const D2R = Math.PI / 180;
  let UID = 0;

  /* ---------------- مكتبة الرسومات (مربع ~200 حول المركز) ----------------
     كل رسمة: مسارات تُرسم بالتسلسل (class=dw) ثم يظهر لونها. */
  const ICONS = {
    sun: c => `<circle class="dw" r="55" fill="#FFC531" stroke="${c}"/>` + [...Array(10)].map((_, k) => {
      const a = k * 36 * D2R; return `<line class="dw" x1="${Math.cos(a) * 72}" y1="${Math.sin(a) * 72}" x2="${Math.cos(a) * 100}" y2="${Math.sin(a) * 100}" stroke="#F29B0D"/>`; }).join(''),
    coin: c => `<circle class="dw" r="70" fill="#F2C230" stroke="#B8860B"/><circle class="dw" r="50" fill="none" stroke="#B8860B"/><path class="dw" d="M-12 -28 h24 M0 -28 v56 M-12 28 h24" stroke="#B8860B" fill="none"/>`,
    seed: c => `<ellipse class="dw" rx="22" ry="14" fill="#8B5A2B" stroke="${c}" transform="rotate(-20)"/>`,
    sprout: c => `<path class="dw" d="M0 60 C0 20 4 0 0 -30" stroke="#2e8b3e" fill="none"/><path class="dw" d="M0 -10 C-40 -30 -55 -5 -50 10 C-30 15 -10 5 0 -10Z" fill="#5cc46b" stroke="#2e8b3e"/><path class="dw" d="M0 -25 C35 -50 55 -30 50 -15 C30 -8 10 -12 0 -25Z" fill="#5cc46b" stroke="#2e8b3e"/>`,
    flower: c => `<path class="dw" d="M0 100 C5 60 -5 30 0 -10" stroke="#2e8b3e" fill="none"/><path class="dw" d="M0 50 C30 30 50 40 45 55 C30 60 10 58 0 50Z" fill="#5cc46b" stroke="#2e8b3e"/>` +
      [...Array(6)].map((_, k) => `<ellipse class="dw" cx="${Math.cos(k * 60 * D2R) * 32}" cy="${-40 + Math.sin(k * 60 * D2R) * 32}" rx="22" ry="14" transform="rotate(${k * 60} ${Math.cos(k * 60 * D2R) * 32} ${-40 + Math.sin(k * 60 * D2R) * 32})" fill="#ff7eb3" stroke="#d63f80"/>`).join('') +
      `<circle class="dw" cy="-40" r="16" fill="#FFC531" stroke="#c98d00"/>`,
    wilted: c => `<path class="dw" d="M0 100 C0 50 10 20 40 10 C60 5 70 20 65 35" stroke="#8a7a3a" fill="none"/><path class="dw" d="M65 35 C50 55 80 70 90 55 C95 45 80 35 65 35Z" fill="#b9a15a" stroke="#7a6a2a"/>`,
    heart: c => `<path class="dw" d="M0 60 C-90 0 -60 -70 0 -25 C60 -70 90 0 0 60Z" fill="#ff4d6d" stroke="#c9184a"/>`,
    star: c => `<path class="dw" d="M0 -80 L22 -25 L80 -25 L33 10 L50 70 L0 35 L-50 70 L-33 10 L-80 -25 L-22 -25Z" fill="#FFD43B" stroke="#d4a106"/>`,
    house: c => `<path class="dw" d="M-80 90 V-10 L0 -80 L80 -10 V90Z" fill="#f6e3c3" stroke="${c}"/><path class="dw" d="M-20 90 V30 H20 V90" fill="#a0522d" stroke="${c}"/><rect class="dw" x="35" y="0" width="30" height="30" fill="#9ed2ff" stroke="${c}"/>`,
    cloud: c => `<path class="dw" d="M-80 30 C-110 30 -110 -20 -75 -20 C-75 -60 -20 -70 0 -40 C20 -75 80 -60 75 -20 C110 -20 110 30 80 30Z" fill="#ffffff" stroke="${c}"/>`,
    rain: c => ICONS.cloud(c) + [-50, -15, 20, 55].map(x => `<line class="dw" x1="${x}" y1="45" x2="${x - 10}" y2="85" stroke="#3a86ff"/>`).join(''),
    fan: c => `<circle class="dw" cy="-40" r="60" fill="#e9f6ff" stroke="${c}"/>` + [0, 120, 240].map(a => `<path class="dw" d="M0 -40 C20 -70 45 -75 50 -60 C40 -45 20 -40 0 -40Z" transform="rotate(${a} 0 -40)" fill="#7fc8f8" stroke="${c}"/>`).join('') +
      `<path class="dw" d="M0 20 V90 M-40 95 H40" stroke="${c}" fill="none"/>`,
    water: c => `<path class="dw" d="M-40 -70 L-30 80 H30 L40 -70Z" fill="#dff3ff" stroke="${c}"/><path class="dw" d="M-37 -20 L-31 75 H31 L37 -20Z" fill="#7cc7ff" stroke="none"/>`,
    book: c => `<path class="dw" d="M0 -60 C-30 -75 -70 -75 -95 -60 V70 C-70 55 -30 55 0 70 C30 55 70 55 95 70 V-60 C70 -75 30 -75 0 -60Z" fill="#fff6dd" stroke="${c}"/><path class="dw" d="M0 -60 V70" stroke="${c}" fill="none"/>`,
    bulb: c => `<path class="dw" d="M-45 -30 C-45 -90 45 -90 45 -30 C45 0 20 10 20 35 H-20 C-20 10 -45 0 -45 -30Z" fill="#FFE066" stroke="${c}"/><path class="dw" d="M-20 50 H20 M-15 65 H15" stroke="${c}" fill="none"/>` +
      [...Array(7)].map((_, k) => { const a = (-150 + k * 20) * D2R; return `<line class="dw" x1="${Math.cos(a) * 70}" y1="${-40 + Math.sin(a) * 70}" x2="${Math.cos(a) * 95}" y2="${-40 + Math.sin(a) * 95}" stroke="#F29B0D"/>`; }).join(''),
    crown: c => `<path class="dw" d="M-70 40 L-80 -40 L-35 0 L0 -60 L35 0 L80 -40 L70 40Z" fill="#F2C230" stroke="#B8860B"/><circle class="dw" cy="-60" r="8" fill="#ff4d6d" stroke="#B8860B"/>`,
    money: c => `<path class="dw" d="M-60 80 C-90 60 -85 -10 -40 -30 L-25 -55 H25 L40 -30 C85 -10 90 60 60 80Z" fill="#c8a165" stroke="#7a5a2b"/><path class="dw" d="M10 0 C-15 -5 -15 20 5 22 C25 25 20 50 -5 45 M3 -10 V55" stroke="#2e7d32" fill="none"/>`,
    apple: c => `<path class="dw" d="M0 -40 C-60 -70 -95 0 -55 60 C-35 85 -15 80 0 70 C15 80 35 85 55 60 C95 0 60 -70 0 -40Z" fill="#e63946" stroke="#9d0208"/><path class="dw" d="M0 -40 C0 -60 8 -75 15 -85" stroke="#6b4226" fill="none"/><path class="dw" d="M5 -60 C25 -85 50 -75 45 -60 C30 -55 15 -55 5 -60Z" fill="#5cc46b" stroke="#2e8b3e"/>`,
    pencil: c => `<path class="dw" d="M-90 25 L50 -30 L75 -20 L85 5 L-55 60Z" fill="#FFC531" stroke="${c}"/><path class="dw" d="M50 -30 L95 -35 L85 5" fill="#f4d19b" stroke="${c}"/>`,
    tree: c => `<path class="dw" d="M-15 100 V20 M15 100 V20" stroke="#7a4b24" fill="none"/><path class="dw" d="M0 30 C-90 40 -100 -40 -50 -55 C-50 -110 50 -110 50 -55 C100 -40 90 40 0 30Z" fill="#6cc36b" stroke="#2e8b3e"/>`,
    zzz: c => `<path class="dw" d="M-40 20 H-10 L-40 50 H-10 M0 -20 H30 L0 10 H30 M40 -60 H65 L40 -35 H65" stroke="${c}" fill="none"/>`,
    question: c => `<path class="dw" d="M-30 -45 C-30 -95 50 -95 45 -45 C42 -15 5 -10 5 20 V35" stroke="${c}" fill="none"/><circle class="dw" cy="65" r="8" fill="${c}" stroke="${c}"/>`,
    bed: c => `<path class="dw" d="M-190 60 V-90 M190 60 V-40" stroke="#7a4b24" stroke-width="14" fill="none"/><rect class="dw" x="-190" y="-10" width="380" height="45" rx="8" fill="#c8915b" stroke="#7a4b24"/><path class="dw" d="M-175 -10 C-175 -45 -120 -50 -105 -20" fill="#ffffff" stroke="${c}"/>`,
    blanket: c => `<path class="dw" d="M-150 -40 C-60 -75 60 -70 175 -45 L178 30 L-150 30Z" fill="#ff8fab" stroke="#c9184a"/><path d="M-110 -20 h40 M-30 -25 h40 M60 -22 h40" stroke="#c9184a" stroke-width="4" fill="none" class="dw"/>`,
    snow: c => [0, 60, 120].map(a => `<path class="dw" d="M0 -60 V60 M-14 -46 L0 -32 L14 -46 M-14 46 L0 32 L14 46" transform="rotate(${a})" stroke="#5aa9e6" fill="none"/>`).join(''),
    alarm: c => `<circle class="dw" r="62" fill="#ffffff" stroke="${c}"/><path class="dw" d="M0 0 V-38 M0 0 L26 14" stroke="${c}" fill="none"/><path class="dw" d="M-70 -50 C-80 -80 -50 -95 -30 -70 M70 -50 C80 -80 50 -95 30 -70" fill="#e63946" stroke="${c}"/><path class="dw" d="M-40 55 L-55 80 M40 55 L55 80" stroke="${c}" fill="none"/>`,
    cup: c => `<path class="dw" d="M-55 -20 H55 L45 75 H-45Z" fill="#ffffff" stroke="${c}"/><path class="dw" d="M55 0 C95 0 95 50 50 50" fill="none" stroke="${c}"/><path class="dw" d="M-50 -8 H50 L47 15 H-47Z" fill="#8b5a2b" stroke="none"/><path class="dw" d="M-25 -40 C-40 -60 -10 -75 -25 -100 M5 -40 C-10 -60 20 -75 5 -100 M35 -40 C20 -60 50 -75 35 -100" stroke="#9aa5b1" fill="none"/>`,
    scarf: c => `<path class="dw" d="M-60 -20 C-20 0 20 0 60 -20 L60 10 C20 30 -20 30 -60 10Z" fill="#e63946" stroke="#9d0208"/><path class="dw" d="M30 10 L40 90 L65 85 L55 5" fill="#e63946" stroke="#9d0208"/><path d="M-40 -5 v18 M-15 2 v18 M10 2 v18" stroke="#ffffff" stroke-width="5" fill="none" class="dw"/>`,
    can: c => `<path class="dw" d="M-70 -40 H30 L40 60 H-80Z" fill="#5cc46b" stroke="#2e8b3e"/><path class="dw" d="M30 -10 L110 -60 L118 -48 L40 15" fill="#5cc46b" stroke="#2e8b3e"/><path class="dw" d="M-70 -30 C-120 -40 -120 40 -78 40" fill="none" stroke="#2e8b3e"/><path class="dw" d="M-50 -40 C-45 -80 15 -80 20 -40" fill="none" stroke="#2e8b3e"/>`,
    drops: c => [[-30, 0], [0, 30], [30, 5], [-12, 60], [18, 75]].map(([x, y]) => `<path class="dw" d="M${x} ${y - 16} C${x - 10} ${y} ${x - 8} ${y + 10} ${x} ${y + 10} C${x + 8} ${y + 10} ${x + 10} ${y} ${x} ${y - 16}Z" fill="#3a86ff" stroke="#1d5fd1" stroke-width="3"/>`).join(''),
    icecream: (c, bite = 0) => { const k = (1 - 0.55 * bite).toFixed(3);   // bite: 0..1 الكرات تصغر أثناء الأكل
      return `<path class="dw" d="M-44 -8 L0 120 L44 -8Z" fill="#e2a85a" stroke="#9a5d22"/>
      <path class="dw" d="M-32 20 L22 -8 M-20 52 L36 22 M-8 86 L26 64 M32 20 L-22 -8 M20 52 L-36 22 M8 86 L-26 64" stroke="#9a5d22" stroke-width="4" fill="none"/>
      <g transform="translate(0 -6) scale(${k}) translate(0 6)">
      <path class="dw" d="M-50 -6 C-66 -40 -40 -74 0 -70 C40 -74 66 -40 50 -6 C30 8 -30 8 -50 -6Z" fill="#fff1e6" stroke="#c9a27a"/>
      <path class="dw" d="M-40 -62 C-56 -96 -24 -130 6 -124 C40 -128 58 -96 42 -62 C24 -52 -22 -52 -40 -62Z" fill="#ff8fab" stroke="#d63f6b"/>
      <path class="dw" d="M-30 -58 C-30 -44 -22 -40 -22 -30 C-22 -22 -12 -22 -12 -32 C-12 -44 -6 -50 -4 -56" fill="#ff8fab" stroke="#d63f6b" stroke-width="4"/>
      <circle class="dw" cx="10" cy="-132" r="12" fill="#e63946" stroke="#9d0208"/><path class="dw" d="M12 -142 C16 -156 26 -162 34 -164" stroke="#2e6b2e" stroke-width="4" fill="none"/></g>`; },
    cone: c => `<path class="dw" d="M-34 -10 L0 90 L34 -10Z" fill="#e8b46a" stroke="#a0662a"/><path class="dw" d="M-22 10 L22 10 M-14 35 L14 35" stroke="#a0662a" fill="none"/>`,
    splat: c => `<path class="dw" d="M-90 10 C-100 -15 -60 -30 -40 -18 C-30 -40 10 -42 20 -22 C45 -38 85 -25 80 0 C110 8 95 30 70 28 C40 40 -20 38 -50 30 C-80 34 -100 24 -90 10Z" fill="#ffb3c6" stroke="#e05780"/><circle class="dw" cx="-10" cy="-30" r="9" fill="#e63946" stroke="#9d0208"/>`,
    cart: c => `<path class="dw" d="M0 -40 V-230" stroke="${c}" fill="none"/><path class="dw" d="M-150 -220 C-100 -300 100 -300 150 -220 Z" fill="#ff8fab" stroke="#c9184a"/><path class="dw" d="M-150 -220 Q-112 -200 -75 -220 Q-37 -200 0 -220 Q37 -200 75 -220 Q112 -200 150 -220" fill="#ffffff" stroke="#c9184a"/>
      <rect class="dw" x="-150" y="-40" width="300" height="130" rx="14" fill="#9ed8ff" stroke="${c}"/><path class="dw" d="M-150 -40 H150" stroke="${c}" stroke-width="12" fill="none"/>
      <path class="dw" d="M-30 0 L-15 50 L0 0Z M-40 0 C-45 -20 -10 -25 -15 0 M5 0 C0 -20 35 -25 30 0" fill="#ffffff" stroke="#c9184a"/>
      <circle class="dw" cx="-95" cy="115" r="30" fill="#ffffff" stroke="${c}"/><circle class="dw" cx="95" cy="115" r="30" fill="#ffffff" stroke="${c}"/>`,
    umbrella: c => `<path class="dw" d="M0 -20 V140 C0 165 -32 165 -32 140" stroke="${c}" stroke-width="9" fill="none"/><path class="dw" d="M-170 -20 C-150 -150 150 -150 170 -20 Q127 -45 85 -20 Q42 -45 0 -20 Q-42 -45 -85 -20 Q-127 -45 -170 -20Z" fill="#4dabf7" stroke="#1864ab"/><path class="dw" d="M0 -128 C-40 -100 -70 -60 -85 -20 M0 -128 C40 -100 70 -60 85 -20" stroke="#1864ab" fill="none"/>`,
    umbrella_broken: c => `<path class="dw" d="M0 -20 V140 C0 165 -32 165 -32 140" stroke="${c}" stroke-width="9" fill="none"/><path class="dw" d="M0 -20 L-120 -150 L-60 -90 L-40 -170 L0 -70 L45 -175 L55 -85 L130 -140 L0 -20Z" fill="#4dabf7" stroke="#1864ab"/><path class="dw" d="M0 -20 L-120 -150 M0 -20 L-40 -170 M0 -20 L45 -175 M0 -20 L130 -140" stroke="#1864ab" fill="none"/>`,
    airbag: c => `<path class="dw" d="M-230 85 C-250 -60 -140 -150 0 -152 C140 -150 250 -60 230 85 Z" fill="#ffd43b" stroke="#c92a2a"/>
      <path class="dw" d="M-150 85 C-170 -20 -110 -110 -55 -140 C-90 -60 -100 20 -85 85Z M85 85 C100 20 90 -60 55 -140 C110 -110 170 -20 150 85Z" fill="#ff6b6b" stroke="#c92a2a"/>
      <path class="dw" d="M-15 -150 C-20 -60 -20 20 -12 85 M15 -150 C20 -60 20 20 12 85" stroke="#c92a2a" fill="none"/>
      <path class="dw" d="M-120 -80 C-100 -115 -60 -132 -20 -136" stroke="#ffffff" stroke-width="14" fill="none" opacity=".85"/>
      <path class="dw" d="M-240 85 H240 V102 H-240Z" fill="#c92a2a" stroke="#862e2e"/><path class="dw" d="M200 40 h28 v-18 h14 v40 h-14 v-10 h-28Z" fill="#adb5bd" stroke="#495057"/>`,
    wind: c => `<path class="dw" d="M-150 -40 H60 C110 -40 110 -100 70 -100 C40 -100 40 -70 60 -65 M-150 10 H120 C170 10 170 70 125 70 C95 70 95 40 115 38 M-130 60 H20" stroke="#74c0fc" stroke-width="10" fill="none"/>`,
    sunface: c => `<circle class="dw" r="80" fill="#FFC531" stroke="#e67700"/>` + [...Array(12)].map((_, k) => { const a = k * 30 * D2R; return `<line class="dw" x1="${Math.cos(a) * 100}" y1="${Math.sin(a) * 100}" x2="${Math.cos(a) * 140}" y2="${Math.sin(a) * 140}" stroke="#F29B0D"/>`; }).join('') +
      `<path class="dw" d="M-38 -18 Q-26 -32 -14 -18 M14 -18 Q26 -32 38 -18 M-34 18 Q0 50 34 18" stroke="#9a4d00" fill="none"/><circle class="dw" cx="-48" cy="12" r="12" fill="#ff8fab" stroke="none"/><circle class="dw" cx="48" cy="12" r="12" fill="#ff8fab" stroke="none"/>`,
    cave: c => `<path class="dw" d="M-260 110 C-270 -60 -170 -210 0 -215 C170 -210 270 -60 260 110Z" fill="#a8a29e" stroke="#57534e"/><path class="dw" d="M-140 110 C-150 0 -90 -100 0 -105 C90 -100 150 0 140 110Z" fill="#292524" stroke="#1c1917"/><path class="dw" d="M-200 -60 l40 -20 M150 -120 l45 10 M180 20 l40 0 M-230 40 l30 10" stroke="#57534e" fill="none"/>`,
    smoke: c => `<circle class="dw" cx="-30" cy="20" r="34" fill="#d6d3d1" stroke="#78716c"/><circle class="dw" cx="20" cy="-10" r="40" fill="#e7e5e4" stroke="#78716c"/><circle class="dw" cx="-10" cy="-55" r="30" fill="#f5f5f4" stroke="#78716c"/>`,
    campfire: c => `<path class="dw" d="M-90 60 L80 20 M-80 20 L90 60" stroke="#7a4b24" stroke-width="22" fill="none"/><path class="dw" d="M0 30 C-60 10 -50 -60 -20 -90 C-20 -50 0 -50 5 -70 C30 -40 55 -30 45 10 C40 30 20 35 0 30Z" fill="#ff922b" stroke="#e8590c"/><path class="dw" d="M0 28 C-25 15 -20 -20 -5 -40 C0 -20 15 -15 20 0 C22 18 12 26 0 28Z" fill="#ffd43b" stroke="#fab005"/>`,
    goalfront: c => `<path class="dw" d="M-200 0 V-260 H200 V0" stroke="${c}" stroke-width="12" fill="none"/>
      <path class="dw net" d="M-150 -258 V0 M-100 -258 V0 M-50 -258 V0 M0 -258 V0 M50 -258 V0 M100 -258 V0 M150 -258 V0 M-198 -205 H198 M-198 -150 H198 M-198 -95 H198 M-198 -40 H198" stroke="${c}" stroke-width="3" fill="none" opacity=".5"/>`,
    goaldoubt: c => `<path class="dw" d="M-200 0 V-260 H200 V0" stroke="${c}" stroke-width="12" fill="none"/>
      <path class="dw" d="M-150 -258 V0 M-75 -258 V0 M0 -258 V0 M75 -258 V0 M150 -258 V0 M-198 -175 H198 M-198 -90 H198" stroke="${c}" stroke-width="3" fill="none" opacity=".45"/>
      <path class="dw" d="M-150 -200 q0 -40 30 -40 q30 0 30 30 q0 22 -30 30 v20 M-120 -112 v6" stroke="#ffd43b" stroke-width="12" fill="none"/>
      <path class="dw" d="M90 -200 q0 -40 30 -40 q30 0 30 30 q0 22 -30 30 v20 M120 -112 v6" stroke="#ffd43b" stroke-width="12" fill="none"/>`,
    goalright: c => `<path class="dw" d="M-200 0 V-260 H200 V0" stroke="${c}" stroke-width="12" fill="none"/>
      <path class="dw" d="M-150 -258 V0 M-75 -258 V0 M0 -258 V0 M75 -258 V0 M150 -258 V0 M-198 -175 H198 M-198 -90 H198" stroke="${c}" stroke-width="3" fill="none" opacity=".45"/>
      <path class="dw" d="M-160 -210 l60 60 M-100 -210 l-60 60" stroke="#ff6b6b" stroke-width="12" fill="none"/>
      <path class="dw" d="M-20 -20 Q60 -60 120 -170" stroke="#ffd43b" stroke-width="9" stroke-dasharray="1 0" fill="none"/>
      <path class="dw" d="M120 -170 l-34 6 M120 -170 l2 34" stroke="#ffd43b" stroke-width="9" fill="none"/>
      <circle class="dw" cx="140" cy="-200" r="32" fill="#ffffff" stroke="#1b1b1b"/><path class="dw" d="M140 -214 l13 9 -5 15 h-16 l-5 -15Z" fill="#1b1b1b" stroke="#1b1b1b"/>`,
    deskside: c => `<path class="dw" d="M-115 -118 H115 V-104 H-115Z" fill="#f4f3ef" stroke="${c}"/><path class="dw" d="M-98 -104 V0 M98 -104 V0 M-98 -66 H50" stroke="${c}" fill="none"/>`,
    board: c => `<rect class="dw" x="-190" y="-120" width="380" height="240" rx="8" fill="#5b6560" stroke="${c}" stroke-width="12"/>
      <circle class="dw" cx="-80" cy="-10" r="44" fill="none" stroke="#f1f1ec" stroke-width="5"/><ellipse class="dw" cx="-80" cy="-10" rx="80" ry="18" fill="none" stroke="#f1f1ec" stroke-width="4"/>
      <circle class="dw" cx="90" cy="-30" r="30" fill="none" stroke="#f1f1ec" stroke-width="5"/><path class="dw" d="M90 -78 V-68 M90 8 V18 M42 -30 H52 M128 -30 H138 M56 -64 l7 7 M117 3 l7 7 M124 -64 l-7 7 M63 3 l-7 7" stroke="#f1f1ec" stroke-width="4" fill="none"/>
      <path class="dw" d="M-20 60 H60 M-20 82 H30" stroke="#f1f1ec" stroke-width="5" stroke-dasharray="14 10" fill="none"/>
      <path class="dw" d="M-150 140 H150" stroke="${c}" stroke-width="8" fill="none"/>`,
    winnight: c => `<rect class="dw" x="-110" y="-130" width="220" height="260" fill="#3c4660" stroke="${c}" stroke-width="10"/><path class="dw" d="M0 -130 V130 M-110 0 H110" stroke="${c}" stroke-width="6" fill="none"/>
      <path class="dw" d="M40 -95 a32 32 0 1 0 22 54 a26 26 0 1 1 -22 -54Z" fill="#f6efc9" stroke="#f6efc9"/><circle class="dw" cx="-60" cy="-80" r="4" fill="#fff" stroke="#fff"/><circle class="dw" cx="-30" cy="60" r="3" fill="#fff" stroke="#fff"/><circle class="dw" cx="70" cy="70" r="4" fill="#fff" stroke="#fff"/>`,
    winday: c => `<rect class="dw" x="-110" y="-130" width="220" height="260" fill="#e7eef3" stroke="${c}" stroke-width="10"/><path class="dw" d="M0 -130 V130 M-110 0 H110" stroke="${c}" stroke-width="6" fill="none"/>
      <circle class="dw" cx="-55" cy="-65" r="28" fill="none" stroke="${c}" stroke-width="5"/><path class="dw" d="M-55 -110 v12 M-55 -32 v12 M-100 -65 h12 M-22 -65 h12" stroke="${c}" stroke-width="4" fill="none"/>`,
    bedg: c => `<path class="dw" d="M-200 60 V-110 M200 60 V-50" stroke="${c}" stroke-width="14" fill="none"/><rect class="dw" x="-200" y="-12" width="400" height="46" rx="8" fill="#e4e2dc" stroke="${c}"/><path class="dw" d="M-185 -12 C-185 -50 -120 -55 -105 -22" fill="#ffffff" stroke="${c}"/>`,
    blanketg: c => `<path class="dw" d="M-110 -20 C-60 -60 60 -60 175 -30 L180 30 L-110 30Z" fill="#d9d6cf" stroke="${c}"/><path class="dw" d="M-60 -32 v58 M20 -40 v66 M100 -36 v62" stroke="${c}" stroke-width="3" fill="none" opacity=".5"/>`,
    phone: c => `<circle class="dw" r="85" fill="rgba(190,225,255,.35)" stroke="none"/><rect class="dw" x="-24" y="-42" width="48" height="84" rx="9" fill="#cfe9ff" stroke="${c}" stroke-width="5"/>`,
    phoneoff: c => `<rect class="dw" x="-24" y="-42" width="48" height="84" rx="9" fill="#2b2b2b" stroke="${c}" stroke-width="5"/>`,
    desklong: c => `<path class="dw" d="M-170 -118 H170 V-104 H-170Z" fill="#f4f3ef" stroke="${c}"/><path class="dw" d="M-152 -104 V0 M152 -104 V0 M-152 -66 H60" stroke="${c}" fill="none"/>`,
    chairside: c => `<g stroke="${c}" stroke-width="8" fill="none" stroke-linecap="round"><path class="dw" d="M-62 -58 H34 M30 -58 V0 M-56 -58 V0 M-58 -58 L-70 -232"/><path class="dw" d="M-70 -232 L-66 -150" stroke-width="14"/></g>`,
    chairfallen: c => `<path class="dw" d="M-120 -8 H60 M-110 -8 V-60 M40 -8 V-55 M60 -8 H190" stroke="${c}" stroke-width="10" fill="none"/>`,
    nightshade: c => `<rect x="-2000" y="-2000" width="4000" height="4000" fill="rgba(25,30,55,.28)"/>`,
    fishbig: c => fishSVG('big', 1, 0, c, false),
    dock: c => `<path class="dw" d="M0 0 H540 V30 H0Z" fill="#efe3c8" stroke="${c}"/>
      <path class="dw" d="M90 0 V30 M190 0 V30 M290 0 V30 M390 0 V30 M490 0 V30" stroke="${c}" stroke-width="4" fill="none"/>
      <path class="dw" d="M40 30 V300 M260 30 V300 M500 30 V300" stroke="${c}" stroke-width="16" fill="none"/>`,
    seaweed: c => `<path class="dw" d="M0 0 C-30 -60 30 -110 0 -170 C-25 -220 20 -260 0 -300" stroke="#3a7d44" stroke-width="10" fill="none"/><path class="dw" d="M30 0 C10 -50 50 -90 30 -150" stroke="#3a7d44" stroke-width="8" fill="none"/>`,
    rock: c => `<path class="dw" d="M-90 0 C-95 -40 -50 -70 -10 -60 C30 -80 85 -50 90 0Z" fill="#c9c3b6" stroke="${c}"/>`,
    fishgrill: (c, b = 0) => b > 0.75 ? `<path class="dw" d="M0 120 V-10" stroke="#7a4b24" stroke-width="8" fill="none"/>
        <path class="dw" d="M0 -80 V40 M-18 -60 h36 M-22 -35 h44 M-22 -10 h44 M-18 15 h36" stroke="${c}" stroke-width="5" fill="none"/><path class="dw" d="M-26 -82 L0 -112 L26 -82Z" fill="none" stroke="${c}"/><path class="dw" d="M-20 40 L0 62 L20 40" fill="none" stroke="${c}"/>`
      : `<path class="dw" d="M0 120 V-10" stroke="#7a4b24" stroke-width="8" fill="none"/>
        <path class="dw" d="M0 ${-110 + 60 * b} C34 ${-80 + 50 * b} 34 20 0 40 C-34 20 -34 ${-80 + 50 * b} 0 ${-110 + 60 * b}Z" fill="#c8722c" stroke="#7a3d12"/>
        <path class="dw" d="M-14 -40 l28 -14 M-16 -10 l32 -14 M-14 18 l28 -12" stroke="#5a2a0a" stroke-width="4" fill="none"/><path class="dw" d="M0 40 L-22 70 L22 70Z" fill="#c8722c" stroke="#7a3d12"/>`,
    goal: c => `<path class="dw" d="M0 0 V-330 H170 L230 0" stroke="${c}" stroke-width="12" fill="none"/>
      <path class="dw net" d="M14 -316 L210 -30 M40 -330 L222 -8 M90 -330 L224 0 M140 -330 L228 0 M10 -250 L190 -250 M10 -170 L205 -170 M10 -90 L218 -90" stroke="${c}" stroke-width="3" fill="none" opacity=".55"/>`,
    ball: c => `<circle class="dw" r="60" fill="#ff8c42" stroke="${c}"/><path class="dw" d="M-60 0 C-20 -25 20 -25 60 0 M0 -60 C25 -20 25 20 0 60" stroke="${c}" fill="none"/>`,
    box: c => `<path class="dw" d="M-70 -50 H70 V60 H-70Z" fill="#d9a76a" stroke="#7a4b24"/><path class="dw" d="M-70 -50 L-50 -75 H90 L70 -50 M70 60 L90 35 V-75" fill="#e8c08c" stroke="#7a4b24"/><path class="dw" d="M-15 -50 V60" stroke="#7a4b24" fill="none"/>`,
    exclaim: c => `<path class="dw" d="M0 -80 V30" stroke="#e63946" fill="none"/><circle class="dw" cy="65" r="10" fill="#e63946" stroke="#e63946"/>`,
  };

  /* ---------------- الوجوه (مركز الرأس، نصف قطر 70) ---------------- */
  function face(kind, ink, t) {
    const blink = (Math.floor(t * 10) % 37 === 0);
    const dot = (x, r = 7) => blink ? `<path d="M${x - 9} -8 h18" stroke="${ink}" stroke-width="5"/>` : `<circle cx="${x}" cy="-8" r="${r}" fill="${ink}"/>`;
    const starEye = x => `<path d="M${x} -30 L${x + 6} -14 L${x + 22} -12 L${x + 9} -2 L${x + 13} 14 L${x} 5 L${x - 13} 14 L${x - 9} -2 L${x - 22} -12 L${x - 6} -14Z" fill="#FFD43B" stroke="#d4a106" stroke-width="3" transform="rotate(${Math.sin(t * 6) * 8} ${x} -8)"/>`;
    switch (kind) {
      case 'sad': return `<path d="M-38 -32 L-12 -24 M38 -32 L12 -24" stroke="${ink}" stroke-width="5"/>${dot(-24, 6)}${dot(24, 6)}<path d="M-22 34 Q0 16 22 34" stroke="${ink}" stroke-width="5" fill="none"/>`;
      case 'shock': return `<circle cx="-25" cy="-10" r="18" fill="#fff" stroke="${ink}" stroke-width="4"/><circle cx="25" cy="-10" r="18" fill="#fff" stroke="${ink}" stroke-width="4"/><circle cx="-25" cy="-8" r="6" fill="${ink}"/><circle cx="25" cy="-8" r="6" fill="${ink}"/><ellipse cy="32" rx="12" ry="16" fill="${ink}"/>`;
      case 'star': return `${starEye(-26)}${starEye(26)}<path d="M-30 18 Q0 58 30 18Z" fill="#7a1f1f" stroke="${ink}" stroke-width="4"/>`;
      case 'laugh': return `<path d="M-36 -6 Q-24 -22 -12 -6 M12 -6 Q24 -22 36 -6" stroke="${ink}" stroke-width="5" fill="none"/><path d="M-30 14 Q0 ${54 + Math.sin(t * 25) * 6} 30 14Z" fill="#7a1f1f" stroke="${ink}" stroke-width="4"/>`;
      case 'angry': return `<path d="M-40 -34 L-12 -20 M40 -34 L12 -20" stroke="${ink}" stroke-width="6"/>${dot(-24, 6)}${dot(24, 6)}<path d="M-20 30 H20" stroke="${ink}" stroke-width="6"/>`;
      case 'drowsy': return `<path d="M-40 -10 H-8 M8 -10 H40" stroke="${ink}" stroke-width="6"/><path d="M-36 -10 A12 8 0 0 0 -12 -10Z M12 -10 A12 8 0 0 0 36 -10Z" fill="${ink}"/><path d="M-14 28 Q0 ${32 + Math.sin(t * 2) * 3} 14 28" stroke="${ink}" stroke-width="5" fill="none"/>`;
      case 'dream': return `<path d="M-36 -6 Q-24 6 -12 -6 M12 -6 Q24 6 36 -6" stroke="${ink}" stroke-width="5" fill="none"/><path d="M-20 22 Q0 40 20 22" stroke="${ink}" stroke-width="5" fill="none"/><path d="M18 30 q4 ${(14 + Math.sin(t * 1.5) * 6).toFixed(1)} 0 ${(22 + Math.sin(t * 1.5) * 8).toFixed(1)} q-6 -4 0 -${(22 + Math.sin(t * 1.5) * 8).toFixed(1)}Z" fill="#cfe8ff" stroke="${ink}" stroke-width="2"/>`;
      case 'sleep': return `<path d="M-36 -8 Q-24 2 -12 -8 M12 -8 Q24 2 36 -8" stroke="${ink}" stroke-width="5" fill="none"/><ellipse cy="30" rx="7" ry="${5 + Math.sin(t * 3) * 3}" fill="${ink}"/>`;
      case 'cry': { const y = 10 + ((t * 120) % 60); return face('sad', ink, t) + `<path d="M-26 ${y} q-6 10 0 14 q6 -4 0 -14Z M26 ${y} q-6 10 0 14 q6 -4 0 -14Z" fill="#3a86ff"/>`; }
      case 'wink': return `${dot(-24)}<path d="M12 -8 Q24 -20 36 -8" stroke="${ink}" stroke-width="5" fill="none"/><path d="M-24 18 Q0 40 24 18" stroke="${ink}" stroke-width="5" fill="none"/>`;
      case 'burnt': return `<circle cx="-24" cy="-8" r="9" fill="#fff"/><circle cx="24" cy="-8" r="9" fill="#fff"/>${blink ? '' : '<circle cx="-24" cy="-8" r="3" fill="#000"/><circle cx="24" cy="-8" r="3" fill="#000"/>'}`;
      case 'lick': return `<path d="M-36 -6 Q-24 -20 -12 -6 M12 -6 Q24 -20 36 -6" stroke="${ink}" stroke-width="5" fill="none"/><path d="M10 18 Q34 22 44 32 Q30 46 8 38Z" fill="#7a1f1f" stroke="${ink}" stroke-width="4"/><path d="M30 30 q${18 + Math.sin(t * 14) * 6} -4 ${22 + Math.sin(t * 14) * 6} 10 q-12 10 -22 0Z" fill="#ff6b8b" stroke="${ink}" stroke-width="3"/><circle cx="-40" cy="22" r="10" fill="#ffb3c1" opacity=".7"/>`;
      case 'chew': return `${dot(-24)}${dot(24)}<ellipse cx="6" cy="26" rx="${16 + Math.sin(t * 20) * 6}" ry="${8 + Math.sin(t * 20) * 5}" fill="#7a1f1f" stroke="${ink}" stroke-width="4"/><circle cx="-40" cy="20" r="10" fill="#ffb3c1" opacity=".7"/><circle cx="40" cy="20" r="10" fill="#ffb3c1" opacity=".7"/>`;
      default: return `${dot(-24)}${dot(24)}<path d="M-26 16 Q0 44 26 16" stroke="${ink}" stroke-width="5" fill="none"/>`; // happy
    }
  }

  /* ---------------- الوضعيات ----------------
     الزوايا بالدرجات: 0 = للأسفل، +90 = للأمام (اتجاه وجه الشخصية)، -90 = للخلف، 180 = للأعلى.
     aL/aR: [عضد، ساعد نسبةً للعضد]، lL/lR: [فخذ، ساق نسبةً للفخذ] (السالب = الركبة تنثني للخلف).
     ph: تقدّم المشهد 0..1 (للحركات ذات المراحل: الرمي والأكل). */
  const sm = p => p * p * (3 - 2 * p);
  // الجسم الملتف (curl): مركزه فوق القدمين بـ BALL_C ونصف قطره BALL_R (بوحدات الشخصية قبل big)
  const BALL_C = 290, BALL_R = 140;
  // الإمساك: حجم الشيء في اليد، ونقطة القبض (بُعدها عن مركز الرسمة للأسفل)، وارتفاع قمته (للأكل)
  const HOLD_S = { fishgrill: 0.7, fishbig: 0.75, umbrella: 0.95, umbrella_broken: 0.95, icecream: 0.62, cone: 0.62, apple: 0.5, cup: 0.5, ball: 0.45, heart: 0.45, box: 0.6, book: 0.5, flower: 0.5, coin: 0.45, can: 0.55, water: 0.5 };
  const GRIP = { fishgrill: 95, umbrella: 135, umbrella_broken: 135, icecream: 60, cone: 60, cup: 10, water: 20, flower: 70, can: -10 };
  const TOP = { fishgrill: 110, icecream: 100, cone: 0, apple: 50, cup: 30, water: 50 };
  const lerp = (a, b, p) => a + (b - a) * p;
  function pose(kind, t, moving, ph) {
    const P = { aL: [14, 8], aR: [-14, -8], lL: [6, -3], lR: [-6, -3], lean: 0, y: 0, sway: 0, fx: {} };
    if (moving && (kind === 'stand' || !kind)) kind = 'walk';
    switch (kind) {
      case 'walk': {   // خطوة هادئة: ذراع عكس الساق، ركبة الساق الخلفية تنثني، اهتزاز خفيف
        const w = Math.sin(t * 7);
        P.lL = [26 * w, -(8 + 34 * Math.max(0, -w))]; P.lR = [-26 * w, -(8 + 34 * Math.max(0, w))];
        P.aL = [-24 * w, 18]; P.aR = [24 * w, 18];
        P.y = -Math.abs(Math.cos(t * 7)) * 9; P.lean = 4; P.fx.walk = true; break; }
      case 'run': {    // جري: ميل للأمام، مرفقان بزاوية قائمة، خطوة واسعة وركبة عالية، خطوط سرعة وغبار
        const w = Math.sin(t * 13);
        P.lL = [48 * w, -(18 + 80 * Math.max(0, -w))]; P.lR = [-48 * w, -(18 + 80 * Math.max(0, w))];
        P.aL = [-50 * w, 100]; P.aR = [50 * w, 100];
        P.y = -Math.abs(Math.cos(t * 13)) * 24; P.lean = 17; P.fx.run = w; break; }
      case 'jump': { const j = Math.abs(Math.sin(t * 5)); P.y = -j * 150; P.aL = [160, 10]; P.aR = [-160, -10]; P.lL = [35 - j * 10, -60 * (1 - j)]; P.lR = [-15 + j * 10, -60 * (1 - j)]; break; }
      case 'wave': case 'greet': {   // تحية: اليد مرفوعة تتحرك يميناً ويساراً مع خطوط حركة
        P.aR = [128, Math.sin(t * 11) * 40 + 10]; P.aL = [10, 6]; P.fx.wave = true; break; }
      case 'cheer': P.aL = [150 + Math.sin(t * 12) * 15, 10]; P.aR = [-150 - Math.sin(t * 12) * 15, -10]; P.y = -Math.abs(Math.sin(t * 6)) * 30; break;
      case 'shiver': P.sway = Math.sin(t * 70) * 5; P.aL = [-35, -120]; P.aR = [35, 120]; P.lL = [3, -4]; P.lR = [-3, -4]; break;
      case 'bend': P.lean = 70; P.aL = [-10, 0]; P.aR = [-25, 0]; P.lL = [10, -6]; P.lR = [-5, -6]; break;
      case 'sit': P.y = 95; P.lL = [95, -90]; P.lR = [85, -80]; P.aL = [30, 40]; P.aR = [-20, -50]; break;
      case 'dance': { const d = Math.sin(t * 8); P.sway = d * 25; P.aL = [90 + d * 60, 40]; P.aR = [-90 + d * 60, -40]; P.lL = [15 + d * 15, -10]; P.lR = [-15 + d * 15, -10]; P.y = -Math.abs(d) * 12; P.lean = d * 8; break; }
      case 'think': P.aR = [-35, -150]; P.aL = [25, 70]; break;
      case 'point': P.aR = [95, -10]; P.aL = [15, 10]; break;
      case 'hold': P.aR = [40, 60]; P.aL = [12, 8]; P.fx.hand = true; break;            // يمسك الشيء أمام صدره
      case 'offer': case 'give': P.aR = [88, 4]; P.aL = [12, 8]; P.fx.hand = true; break;  // يقدّم: ذراع ممدودة والشيء في الكف
      case 'carry': P.aR = [55, 50]; P.aL = [65, 40]; P.lean = -4; P.fx.hand = true; break; // يحمل بيديه الاثنتين
      case 'eat': case 'drink': {   // يرفع الشيء إلى فمه ويعيده مراراً
        const u = (t % 1.3) / 1.3, k = u < 0.25 ? sm(u / 0.25) : u < 0.6 ? 1 : u < 0.85 ? 1 - sm((u - 0.6) / 0.25) : 0;
        P.aR = [lerp(40, 112, k), lerp(60, 108, k)]; P.aL = [12, 8]; P.lean = -3 * k; P.fx.hand = true; P.fx.eat = k; break; }
      case 'clap': { const k = (Math.sin(t * 14) + 1) / 2; P.aL = [80, -15 + 30 * k]; P.aR = [100, 15 - 30 * k]; P.fx.clap = k; break; }
      case 'umbrella': {   // يمسك المظلة فوق رأسه (مع المشي تُضاف السيقان تلقائياً)
        P.aR = [172 + Math.sin(t * 3) * 3, -6]; P.aL = [14, 8]; P.fx.hand = true; break; }
      case 'dangle': {     // معلّق في الهواء بالمظلة: ذراع للأعلى، ساقان تتأرجحان
        const d = Math.sin(t * 5); P.aR = [176, 0]; P.aL = [120 + d * 25, 20]; P.lL = [18 + d * 22, -25 - d * 10]; P.lR = [-14 - d * 22, -20 + d * 10]; P.fx.hand = true; break; }
      case 'fall': {       // سقوط سريع: ذراعان تلوّحان للأعلى، ساقان متباعدتان، خطوط سرعة فوقه
        const d = Math.sin(t * 16); P.aL = [150 + d * 25, 30]; P.aR = [-150 - d * 25, -30]; P.lL = [35, -40 + d * 15]; P.lR = [-30, -30 - d * 15]; P.fx.fall = true; break; }
      case 'curl':         // ملتف ككرة (للتدحرج): ركبتان للصدر، ذراعان تحضنان
        P.lL = [150, -150]; P.lR = [140, -140]; P.aL = [60, 90]; P.aR = [80, 80]; P.lean = 25; P.y = -40; break;
      case 'kick': case 'kick_soft': {   // ركل: سحب الساق للخلف ← ضربة سريعة ← متابعة (kick_soft أخف)
        const p = ph == null ? (t % 2) / 2 : ph, hard = kind === 'kick';
        const back = hard ? -65 : -30, fwd = hard ? 105 : 50, kb = hard ? -95 : -55;
        let th, kn, ln;
        if (p < 0.4) { const k = sm(p / 0.4); th = lerp(0, back, k); kn = lerp(0, kb, k); ln = lerp(0, hard ? 10 : 4, k); }
        else if (p < 0.5) { const k = sm((p - 0.4) / 0.1); th = lerp(back, fwd * 0.7, k); kn = lerp(kb, 0, k); ln = lerp(hard ? 10 : 4, -6, k); P.fx.kick = true; }
        else { const k = sm(clamp((p - 0.5) / 0.3)); th = lerp(fwd * 0.7, fwd, k); kn = 0; ln = lerp(-6, hard ? -14 : -4, k);
          if (p > 0.8) { const r = sm((p - 0.8) / 0.2); th = lerp(fwd, 4, r); ln = lerp(hard ? -14 : -4, 0, r); } }
        P.lR = [th, kn]; P.lL = [-6, -4]; P.lean = ln;
        P.aL = [lerp(20, 70, clamp(th / 100 + 0.3)), 20]; P.aR = [lerp(-20, -70, clamp(th / 100 + 0.3)), -15];
        break; }
      case 'rod': P.aR = [95, 30]; P.aL = [75, 20]; P.fx.hand = true; P.fx.rodA = 125; break;          // يمسك الصنارة أمامه
      case 'sit_rod': P.y = 95; P.lL = [95, -90]; P.lR = [85, -80]; P.aR = [95, 30]; P.aL = [75, 20]; P.fx.rodA = 120; break;
      case 'pull': P.lean = -14; P.aR = [140, -5]; P.aL = [120, 0]; P.lL = [28, -8]; P.lR = [-12, -4]; P.fx.rodA = 155; break;   // يسحب بقوة
      case 'reel': P.lean = -12; P.aR = [135, -5]; P.aL = [100 + 25 * Math.sin(t * 16), 30 + 20 * Math.cos(t * 16)]; P.lL = [28, -8]; P.lR = [-12, -4]; P.fx.rodA = 150; break;
      case 'yank': { const p = ph == null ? 0.5 : ph, k = sm(clamp((p - 0.35) / 0.12)); P.aR = [lerp(95, 165, k), lerp(30, -10, k)]; P.aL = [lerp(75, 140, k), 0]; P.lean = -10 * k; P.fx.rodA = lerp(125, 168, k); break; }
      case 'sit_chair': P.y = 60; P.lL = [90, -90]; P.lR = [84, -84]; P.aR = [72, 38]; P.aL = [62, 48]; P.lean = 4; break;
      case 'nod': { const p = ph == null ? 0.5 : ph, cyc = (t * 0.55) % 1, v = cyc < 0.82 ? sm(cyc / 0.82) : 1 - sm((cyc - 0.82) / 0.18);
        P.y = 60; P.lL = [90, -90]; P.lR = [84, -84]; P.aR = [72, 38]; P.aL = [62, 48]; P.lean = 4 + v * lerp(14, 42, p); P.fx.headTilt = v * 18; break; }
      case 'sleep_desk': P.y = 60; P.lL = [90, -90]; P.lR = [84, -84]; P.lean = 56 + Math.sin(t * 1.8) * 2; P.aR = [118, 72]; P.aL = [112, 78]; P.fx.headTilt = 28; break;
      case 'startle': P.y = 20; P.lL = [118, -50]; P.lR = [106, -40]; P.aR = [165 + Math.sin(t * 30) * 12, 30]; P.aL = [-160 - Math.sin(t * 30) * 12, -30]; P.lean = -18; break;
      case 'raise_hand': P.y = 60; P.lL = [90, -90]; P.lR = [84, -84]; P.aR = [176 + Math.sin(t * 9) * 7, -4]; P.aL = [62, 48]; P.lean = 2; P.fx.wave = true; break;
      case 'laughsit': P.y = 60; P.lL = [90, -90]; P.lR = [84, -84]; P.aR = [25, 95]; P.aL = [18, 100]; P.sway = Math.sin(t * 28) * 4; P.lean = 8 + Math.sin(t * 14) * 5; break;
      case 'knock': { const k = Math.max(0, Math.sin(t * 13)); P.lean = 32; P.y = 30; P.lL = [20, -40]; P.lR = [-2, -38]; P.aR = [lerp(16, 72, k), lerp(0, -45, k)]; P.aL = [-15, 25]; P.fx.knock = k < 0.08; break; }
      case 'hips': P.aR = [40, -120]; P.aL = [40, -120]; break;
      case 'look_up': P.aR = [150, 30]; P.aL = [-20, 10]; P.lean = -10; P.fx.lookup = true; break;
      case 'throw': {   // رمي: تحضير للخلف ← قذف سريع للأمام ← متابعة
        const p = ph == null ? (t % 2) / 2 : ph;
        let up, lo, ln;
        if (p < 0.45) { const k = sm(p / 0.45); up = lerp(35, -150, k); lo = lerp(20, -20, k); ln = lerp(0, -10, k); }
        else if (p < 0.55) { const k = sm((p - 0.45) / 0.1); up = lerp(-150, 125, k); lo = lerp(-20, 10, k); ln = lerp(-10, 16, k); P.fx.swing = true; }
        else { const k = sm((p - 0.55) / 0.45); up = lerp(125, 55, k); lo = lerp(10, 20, k); ln = lerp(16, 6, k); }
        P.aR = [up, lo]; P.aL = [-20, 10]; P.lean = ln; P.lL = [18, -6]; P.lR = [-14, -10];
        P.fx.hand = p < 0.5; P.fx.thrown = p >= 0.5; break; }
    }
    // المشي مع الإمساك: سيقان المشي + وضعية اليد كما هي (يمشي حاملاً الشيء أو مقدّماً إياه)
    if (moving && ['rod', 'hold', 'offer', 'give', 'carry', 'eat', 'drink', 'wave', 'greet', 'point'].includes(kind)) {
      const W = pose('walk', t, true, ph); P.lL = W.lL; P.lR = W.lR; P.y = W.y; P.lean = Math.max(P.lean, 3);
    }
    return P;
  }

  function limb(x, y, a1, a2, L1, L2) {
    const x1 = x + Math.sin(a1 * D2R) * L1, y1 = y + Math.cos(a1 * D2R) * L1;
    const x2 = x1 + Math.sin((a1 + a2) * D2R) * L2, y2 = y1 + Math.cos((a1 + a2) * D2R) * L2;
    return { d: `M${x} ${y} L${x1.toFixed(1)} ${y1.toFixed(1)} L${x2.toFixed(1)} ${y2.toFixed(1)}`, ex: x2, ey: y2, a: a1 + a2 };
  }
  const foot = (L, body) => { const a = (L.a + 90) * D2R;   // القدم تشير للأمام عمودياً على الساق
    return `<path d="M${L.ex.toFixed(1)} ${L.ey.toFixed(1)} l${(Math.sin(a) * 26).toFixed(1)} ${(Math.cos(a) * 26).toFixed(1)}" stroke="${body}" stroke-width="9" fill="none"/>`; };
  const hand = (A, body, burnt, paper) => `<circle cx="${A.ex.toFixed(1)}" cy="${A.ey.toFixed(1)}" r="11" fill="${burnt ? '#111' : (paper || '#fff')}" stroke="${body}" stroke-width="6"/>`;

  function charSVG(c, t, faceKind, poseKind, moving, ph) {
    const ink = INK[c.ink] || c.ink || INK.pencil;
    const P = pose(poseKind, t, moving, ph);
    const burnt = faceKind === 'burnt', body = burnt ? '#111' : ink;
    const hipY = -120, neckY = -255, headY = -335, R = 70;
    // الجذع يميل حول الورك
    const lx = Math.sin(P.lean * D2R) * (hipY - neckY), ly = Math.cos(P.lean * D2R) * (hipY - neckY);
    const nx = lx, ny = hipY - ly, hx = Math.sin(P.lean * D2R) * (hipY - headY), hy = hipY - Math.cos(P.lean * D2R) * (hipY - headY);
    const shirt = c.shirt ? `<path d="M${nx - 28} ${ny + 8} L${-26} ${hipY + 6} L26 ${hipY + 6} L${nx + 28} ${ny + 8}Z" fill="${c.shirt}" stroke="${body}" stroke-width="7" stroke-linejoin="round"/>` : '';
    const LL = limb(0, hipY, P.lL[0], P.lL[1], 62, 60), LR = limb(0, hipY, P.lR[0], P.lR[1], 62, 60);
    const AL = limb(nx, ny + 15, P.aL[0], P.aL[1], 52, 50), AR = limb(nx, ny + 15, P.aR[0], P.aR[1], 52, 50);
    let extra = '', front = '';
    if (P.fx.run != null) {   // خطوط سرعة خلف الجسم + غبار عند القدم الخلفية
      const fl = 0.55 + 0.45 * Math.sin(t * 40);
      extra += [[-300, 0], [-220, 30], [-150, -20]].map(([y, dx], k) => `<path d="M${-110 + dx} ${y} h${-(110 + k * 30)}" stroke="${body}" stroke-width="6" opacity="${(fl * (0.7 - k * 0.15)).toFixed(2)}"/>`).join('');
      const u = (t * 13 / Math.PI) % 1;
      extra += `<g opacity="${(1 - u).toFixed(2)}" fill="#fff" stroke="${body}" stroke-width="4"><circle cx="${-70 - u * 60}" cy="${-8 - u * 20}" r="${10 + u * 16}"/><circle cx="${-110 - u * 70}" cy="${-4 - u * 10}" r="${7 + u * 10}"/></g>`;
    }
    if (P.fx.fall) {   // خطوط سرعة عمودية فوق الرأس
      const fl = 0.5 + 0.5 * Math.sin(t * 45);
      extra += [-60, -10, 45].map((x, k) => `<path d="M${x} ${-440 - k * 20} v${-(120 + k * 40)}" stroke="${body}" stroke-width="6" opacity="${(fl * (0.75 - k * 0.15)).toFixed(2)}"/>`).join('');
    }
    if (P.fx.wave) {   // خطوط حركة حول اليد المحيّية
      const o = Math.sin(t * 11) * 0.5 + 0.5;
      front += `<g stroke="${body}" stroke-width="5" fill="none" opacity="${(0.4 + 0.5 * o).toFixed(2)}"><path d="M${AR.ex - 38} ${AR.ey - 20} q-14 20 0 40"/><path d="M${AR.ex + 38} ${AR.ey - 20} q14 20 0 40"/><path d="M${AR.ex - 56} ${AR.ey - 30} q-18 30 0 60"/></g>`;
    }
    if (P.fx.swing) front += `<g stroke="${body}" stroke-width="6" fill="none" opacity=".6"><path d="M${nx - 60} ${ny - 120} Q${nx + 60} ${ny - 190} ${nx + 150} ${ny - 40}"/><path d="M${nx - 30} ${ny - 80} Q${nx + 50} ${ny - 140} ${nx + 120} ${ny - 20}"/></g>`;
    if (P.fx.kick) front += `<g stroke="${body}" stroke-width="6" fill="none" opacity=".6"><path d="M${LR.ex - 120} ${LR.ey - 70} Q${LR.ex - 40} ${LR.ey + 30} ${LR.ex + 40} ${LR.ey - 10}"/><path d="M${LR.ex - 90} ${LR.ey - 100} Q${LR.ex - 20} ${LR.ey} ${LR.ex + 30} ${LR.ey - 40}"/></g>`;
    if (P.fx.knock) front += `<g stroke="${body}" stroke-width="5" opacity=".8"><path d="M${AR.ex - 34} ${AR.ey + 6} l-22 -10 M${AR.ex + 34} ${AR.ey + 6} l22 -10 M${AR.ex - 26} ${AR.ey - 16} l-16 -20 M${AR.ex + 26} ${AR.ey - 16} l16 -20"/></g>`;
    if (P.fx.clap > 0.85) front += `<g stroke="${body}" stroke-width="5" opacity=".7"><path d="M${AR.ex + 30} ${AR.ey - 30} l20 -18 M${AR.ex + 36} ${AR.ey} h26 M${AR.ex + 30} ${AR.ey + 30} l20 18"/></g>`;
    // الشيء المُمسك: يُرسم قبل الكف فتبدو اليد قابضة عليه، وعند الأكل يصعد إلى الفم
    let held = '', grip = '';
    if (c.hold && P.fx.hand !== false && !(P.fx.thrown) && ICONS[c.hold]) {
      const hs = c.hold_s || HOLD_S[c.hold] || 0.5, G = (GRIP[c.hold] || 0) * hs;
      let ox = 0, oy = -G;
      if (P.fx.eat != null) {   // الفم أمام الوجه: نقرّب قمة الشيء منه تدريجياً
        const mx = hx + 52, my = hy + 22, top = (TOP[c.hold] || 60) * hs;
        ox = lerp(0, mx - AR.ex, P.fx.eat); oy = lerp(-G, my - AR.ey + top * 0.55, P.fx.eat);
      }
      held = `<g transform="translate(${(AR.ex + ox).toFixed(1)} ${(AR.ey + oy).toFixed(1)}) scale(${hs})">${ICONS[c.hold](ink, c.bite != null ? c.bite : (P.fx.eat != null ? clamp((ph || 0) * 0.95) : 0))}</g>`;
      grip = `<path d="M${(AR.ex - 9).toFixed(1)} ${(AR.ey - 6).toFixed(1)} q9 -7 18 0 M${(AR.ex - 9).toFixed(1)} ${(AR.ey + 3).toFixed(1)} q9 -7 18 0" stroke="${body}" stroke-width="3.5" fill="none"/>`;
    }
    const svg = `<g transform="translate(${P.sway} ${P.y})" stroke-linecap="round" stroke-linejoin="round">${extra}
      <path d="${LL.d}" stroke="${body}" stroke-width="9" fill="none"/>${foot(LL, body)}
      <path d="${LR.d}" stroke="${body}" stroke-width="9" fill="none"/>${foot(LR, body)}
      <path d="M0 ${hipY} L${nx.toFixed(1)} ${ny.toFixed(1)}" stroke="${body}" stroke-width="9"/>${shirt}
      ${c.scarf ? `<g transform="translate(${nx.toFixed(1)} ${(ny + 6).toFixed(1)})"><path d="M-46 -12 C-15 6 15 6 46 -12 L46 14 C15 30 -15 30 -46 14Z" fill="#e63946" stroke="#9d0208" stroke-width="5"/>
        <path d="M18 14 L${26 + Math.sin(t * 6) * 6} 80 L${46 + Math.sin(t * 6) * 6} 76 L38 10" fill="#e63946" stroke="#9d0208" stroke-width="5"/></g>` : ''}
      <path d="${AL.d}" stroke="${body}" stroke-width="8" fill="none"/>${hand(AL, body, burnt, c.paper)}
      <g transform="translate(${hx.toFixed(1)} ${hy.toFixed(1)}) rotate(${P.lean * 0.4 + (P.fx.headTilt || 0)})">
        <circle r="${R}" fill="${burnt ? '#111' : (c.paper || '#fff')}" stroke="${body}" stroke-width="7"/>
        <path d="M-10 -68 q-6 -22 -2 -30 M4 -70 q2 -24 10 -30 M16 -66 q10 -16 20 -18" stroke="${body}" stroke-width="5" fill="none"/>
        ${P.fx.lookup ? '<g transform="translate(6 -22)">' : '<g>'}${face(P.fx.eat > 0.6 ? (c.hold === 'icecream' ? 'lick' : 'chew') : faceKind, burnt ? '#fff' : ink, t)}</g>${c.glasses ? `<g stroke="${ink}" stroke-width="4" fill="rgba(255,255,255,.25)"><circle cx="-24" cy="-8" r="19"/><circle cx="24" cy="-8" r="19"/><path d="M-5 -10 Q0 -14 5 -10 M-43 -10 L-66 -16" fill="none"/></g>` : ''}
      </g>
      ${held}<path d="${AR.d}" stroke="${body}" stroke-width="8" fill="none"/>${hand(AR, body, burnt, c.paper)}${grip}${front}</g>`;
    let tip = null, rodSvg = '';
    if (c.rod) {   // صنارة من الكف: زاويتها حسب الوضعية (0 للأسفل، 90 للأمام، 180 للأعلى)، وتنحني عند الشد
      const a = (P.fx.rodA != null ? P.fx.rodA : (poseKind === 'throw' ? AR.a + 15 : (P.fx.walk ? 165 : 125))) * D2R, L = 235;
      const bend = c._bend || 0, ex = AR.ex + Math.sin(a) * L, ey = AR.ey + Math.cos(a) * L;
      const tx = AR.ex + Math.sin(a - bend * 0.9) * L * (1 - 0.12 * bend), ty2 = AR.ey + Math.cos(a - bend * 0.9) * L * (1 - 0.12 * bend) + bend * 60;
      const cx = AR.ex + Math.sin(a) * L * 0.62, cy = AR.ey + Math.cos(a) * L * 0.62;
      rodSvg = `<path d="M${AR.ex.toFixed(1)} ${AR.ey.toFixed(1)} Q${cx.toFixed(1)} ${cy.toFixed(1)} ${tx.toFixed(1)} ${ty2.toFixed(1)}" stroke="#7a4b24" stroke-width="7" fill="none" stroke-linecap="round"/>
        <circle cx="${(AR.ex + Math.sin(a) * 30).toFixed(1)}" cy="${(AR.ey + Math.cos(a) * 30).toFixed(1)}" r="9" fill="#fff" stroke="${body}" stroke-width="4"/>`;
      tip = { x: tx + P.sway, y: ty2 + P.y };
    }
    const svg2 = rodSvg ? svg.replace(/<\/g>$/, rodSvg + `<path d="${AR.d}" stroke="${body}" stroke-width="8" fill="none"/>${hand(AR, body, burnt, c.paper)}</g>`) : svg;
    const chair = c.chair && ['sit_chair', 'nod', 'sleep_desk', 'startle', 'raise_hand', 'laughsit', 'clap', 'wink'].includes(poseKind) ? `<g stroke="${body}" stroke-width="8" fill="none" stroke-linecap="round"><path d="M-62 -58 H34 M30 -58 V0 M-56 -58 V0 M-58 -58 L-70 -232"/><path d="M-70 -232 L-66 -150" stroke-width="14"/></g>` : '';
    return { svg: chair + svg2, hand: { x: AR.ex + P.sway, y: AR.ey + P.y }, tip };
  }
  // موضع اليد اليمنى لحظة الإفلات في الرمي (لنقطة بداية طيران الشيء)
  function releaseHand(c) { const r = charSVG(c, 0, 'happy', 'throw', false, 0.5); return r.hand; }

  /* ---------------- التنين (شخصية: kind=dragon) ----------------
     الأصل عند القدمين على الأرض، الوجه نحو +x. الوضعيات: idle peek fire fly. الوجوه: happy sad cry shock laugh sneeze */
  function dragonSVG(c, t, faceKind, poseKind, ph) {
    const ink = INK[c.ink] || c.ink || INK.pencil, G = '#7bd389', GD = '#2f9e44', BEL = '#eaf7c9';
    const fly = poseKind === 'fly', fire = poseKind === 'fire';
    const bob = fly ? Math.sin(t * 6) * 18 : Math.sin(t * 2.5) * 3;
    const flap = fly ? Math.sin(t * 12) * 32 : Math.sin(t * 3) * 8;
    const legs = fly ? `<path d="M-40 -45 q-6 22 10 26 M40 -45 q-6 22 10 26" stroke="${GD}" stroke-width="16" fill="none" stroke-linecap="round"/>`
      : `<path d="M-45 -40 V0 M45 -40 V0" stroke="${GD}" stroke-width="22" stroke-linecap="round"/><path d="M-62 0 H-28 M28 0 H62" stroke="${ink}" stroke-width="7" stroke-linecap="round"/>`;
    const wing = `<g transform="rotate(${(-flap).toFixed(1)} -20 -170)"><path d="M-20 -170 C-60 -280 -170 -300 -210 -250 C-170 -240 -160 -215 -150 -200 C-120 -215 -95 -195 -85 -175 C-60 -190 -40 -180 -20 -170Z" fill="#a9e34b" stroke="${GD}" stroke-width="6"/></g>`;
    const tail = `<path d="M-100 -90 C-180 -70 -230 -30 -250 -100" stroke="${GD}" stroke-width="30" fill="none" stroke-linecap="round"/><path d="M-268 -110 L-240 -150 L-228 -98Z" fill="#fab005" stroke="${ink}" stroke-width="5"/>`;
    const spikes = [-60, -20, 20].map(x => `<path d="M${x - 14} ${-188 + Math.abs(x) * 0.25} l14 -28 l14 28Z" fill="#fab005" stroke="${ink}" stroke-width="4"/>`).join('');
    const blink = Math.floor(t * 10) % 41 === 0;
    let eyes, mouth = '', extra = '';
    const E = (x, y, r) => `<circle cx="${x}" cy="${y}" r="${r}" fill="#fff" stroke="${ink}" stroke-width="5"/>`;
    switch (faceKind) {
      case 'shock': eyes = E(122, -250, 22) + `<circle cx="126" cy="-250" r="8" fill="${ink}"/>`; mouth = `<ellipse cx="200" cy="-205" rx="14" ry="18" fill="#7a1f1f" stroke="${ink}" stroke-width="4"/>`; break;
      case 'laugh': eyes = `<path d="M104 -250 q16 -18 32 0" stroke="${ink}" stroke-width="6" fill="none"/>`; mouth = `<path d="M165 -215 Q200 ${-170 + Math.sin(t * 25) * 6} 228 -210Z" fill="#7a1f1f" stroke="${ink}" stroke-width="4"/>`; break;
      case 'sneeze': eyes = `<path d="M104 -262 l26 12 l-26 12" stroke="${ink}" stroke-width="6" fill="none"/>`; mouth = `<path d="M170 -212 Q205 -195 230 -214" stroke="${ink}" stroke-width="6" fill="#7a1f1f"/>`; break;
      case 'sad': case 'cry':
        eyes = (blink ? `<path d="M108 -248 h28" stroke="${ink}" stroke-width="5"/>` : E(122, -248, 15) + `<circle cx="124" cy="-244" r="6" fill="${ink}"/>`) + `<path d="M100 -275 L140 -266" stroke="${ink}" stroke-width="5"/>`;
        mouth = `<path d="M172 -196 Q195 -214 218 -196" stroke="${ink}" stroke-width="5" fill="none"/>`;
        if (faceKind === 'cry') { const y = -232 + ((t * 110) % 70); extra = `<path d="M120 ${y} q-8 13 0 18 q8 -5 0 -18Z M132 ${y + 30} q-7 11 0 15 q7 -4 0 -15Z" fill="#3a86ff"/>`; }
        break;
      default: eyes = blink ? `<path d="M108 -248 h28" stroke="${ink}" stroke-width="5"/>` : E(122, -248, 16) + `<circle cx="126" cy="-246" r="7" fill="${ink}"/><circle cx="129" cy="-250" r="2.5" fill="#fff"/>`;
        mouth = `<path d="M172 -212 Q198 -192 224 -210" stroke="${ink}" stroke-width="5" fill="none"/>`;
    }
    let flame = '';
    if (fire || faceKind === 'sneeze') {
      const L = (c.fire || 260) * (fire ? 1 : 0), f1 = Math.sin(t * 30) * 12, f2 = Math.cos(t * 23) * 10;
      if (L > 0) flame = `<path d="M228 -212 C${260 + L * 0.3} ${-270 + f1} ${228 + L * 0.75} ${-280 + f2} ${228 + L} ${-215 + f1} C${228 + L * 0.75} ${-150 + f2} ${260 + L * 0.3} ${-160 - f1} 228 -212Z" fill="#ff922b" stroke="#e8590c" stroke-width="5"/>
        <path d="M232 -212 C${255 + L * 0.25} ${-245 + f2} ${232 + L * 0.55} ${-250 - f1} ${232 + L * 0.72} ${-214 + f2} C${232 + L * 0.55} ${-180 + f1} ${255 + L * 0.25} ${-185} 232 -212Z" fill="#ffd43b"/>`;
    }
    const svg = `<g transform="translate(0 ${(fly ? bob - 60 : bob * 0.3).toFixed(1)})" stroke-linejoin="round">
      ${tail}${wing}${legs}
      <ellipse cx="0" cy="-110" rx="112" ry="86" fill="${G}" stroke="${ink}" stroke-width="7"/>
      <ellipse cx="28" cy="-96" rx="60" ry="56" fill="${BEL}" stroke="${GD}" stroke-width="4"/>${spikes}
      <path d="M60 -150 C80 -190 95 -205 110 -210" stroke="${G}" stroke-width="60" stroke-linecap="round"/>
      <circle cx="122" cy="-238" r="68" fill="${G}" stroke="${ink}" stroke-width="7"/>
      <ellipse cx="190" cy="-214" rx="54" ry="36" fill="${G}" stroke="${ink}" stroke-width="7"/>
      <circle cx="210" cy="-226" r="5" fill="${ink}"/><circle cx="226" cy="-222" r="5" fill="${ink}"/>
      <path d="M92 -296 l-10 -40 l26 30 M136 -302 l6 -42 l14 38" fill="#fab005" stroke="${ink}" stroke-width="5"/>
      <circle cx="150" cy="-200" r="13" fill="#ff8fab" opacity=".7"/>
      ${eyes}${mouth}${extra}${flame}</g>`;
    return { svg, head: { x: 122, y: -238 } };
  }

  /* ---------------- بناء المشهد ---------------- */
  function build(s, cam, i) {
    const d = s.doodle || {}, U = ++UID;
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 1080 1920');
    svg.setAttribute('style', 'position:absolute;left:0;top:0;width:1080px;height:1920px;overflow:visible');
    const ground = d.ground != null ? d.ground : 1560;
    const gink = INK[d.ink] || INK.pencil;
    svg.innerHTML = `<defs><filter id="boil${U}" x="-5%" y="-5%" width="110%" height="110%">
        <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="2" seed="1"/>
        <feDisplacementMap in="SourceGraphic" scale="5" xChannelSelector="R" yChannelSelector="G"/></filter></defs>
      <g filter="url(#boil${U})">
        ${d.noground ? '' : `<path d="M40 ${ground + 6} C300 ${ground - 4} 700 ${ground + 10} 1040 ${ground}" stroke="${gink}" stroke-width="5" fill="none" stroke-linecap="round" opacity=".55"/>
        <path d="M120 ${ground + 40} h60 M560 ${ground + 30} h90 M860 ${ground + 46} h50" stroke="${gink}" stroke-width="3" opacity=".3" stroke-linecap="round"/>`}
        <g class="draws"></g><g class="chars"></g><g class="front"></g><g class="think"></g></g>`;
    cam.appendChild(svg);
    const R = { svg, turb: svg.querySelector('feTurbulence'), draws: [], chars: [], d, ground };
    // الرسومات
    const dg = svg.querySelector('.draws');
    (d.draws || []).forEach((w, k) => {
      const fn = ICONS[w.icon]; if (!fn) return;
      const g = document.createElementNS(NS, 'g');
      g.innerHTML = fn(gink);
      g.querySelectorAll('.dw').forEach(p => { p.setAttribute('pathLength', '1'); p.setAttribute('stroke-width', p.getAttribute('stroke-width') || '7'); p.style.strokeDasharray = '1 1'; p.style.strokeDashoffset = '1'; p.dataset.fill = p.getAttribute('fill') || 'none'; });
      (w.front ? svg.querySelector('.front') : dg).appendChild(g);   // ^ : أمام الشخصية (البطانية فوق الجسم)
      R.draws.push({ g, w, paths: [...g.querySelectorAll('.dw')], at: s.start + (w.delay || 0) + 0.15 + k * 0.12 });
    });
    // الشخصيات
    const cg = svg.querySelector('.chars');
    (d.chars || []).forEach(c => { if (d.paper && !c.paper) c.paper = d.paper; const g = document.createElementNS(NS, 'g'); R.chars.push({ g, c }); });
    R.chars.slice().sort((a, b) => (a.c.z || 0) - (b.c.z || 0)).forEach(o => cg.appendChild(o.g));   // z= ترتيب الرسم (الأصغر خلف)
    // فقاعة التفكير
    if (d.think && d.think.length && R.chars.length) {
      const g = document.createElementNS(NS, 'g'); svg.querySelector('.think').appendChild(g);
      const icons = d.think.map((n, k) => ICONS[n] ? (/^goal/.test(n) ? `<g transform="translate(${(k - (d.think.length - 1) / 2) * 150} 92) scale(.74)">${ICONS[n](gink)}</g>` : `<g transform="translate(${(k - (d.think.length - 1) / 2) * 150} 0) scale(.62)">${ICONS[n](gink)}</g>`) : '').join('');
      g.innerHTML = `<path d="M-230 40 C-290 40 -290 -40 -230 -45 C-230 -120 -120 -135 -80 -95 C-50 -150 60 -150 90 -95 C150 -130 240 -100 230 -40 C290 -30 285 50 225 55 C230 110 130 125 100 90 C60 135 -60 135 -90 95 C-140 130 -240 110 -230 40Z" fill="#fffef6" stroke="${gink}" stroke-width="6"/>
        <g transform="translate(0 -5)">${icons}</g>
        <circle cx="-120" cy="150" r="18" fill="#fffef6" stroke="${gink}" stroke-width="5"/><circle cx="-150" cy="200" r="11" fill="#fffef6" stroke="${gink}" stroke-width="4"/>`;
      R.think = g;
    }
    // فقاعة الكلام (HTML لتشكيل العربية بشكل صحيح)
    if (d.say) {
      const b = document.createElement('div');
      b.textContent = d.say;
      b.style.cssText = `position:absolute;left:0;top:0;max-width:620px;padding:22px 34px;background:#fff;border:6px solid ${gink};border-radius:46px;
        font:800 50px ${(TL_FONT())},Tajawal,sans-serif;color:#1b1b1b;direction:rtl;white-space:nowrap;box-shadow:6px 8px 0 rgba(0,0,0,.12)`;
      cam.appendChild(b); R.say = b;
    }
    return R;
  }
  const TL_FONT = () => { const f = (window.TIMELINE && window.TIMELINE.font) || ''; return ({ scheherazade: "'Scheherazade New'", amiri: 'Amiri', baloo: "'Baloo Bhaijaan 2'", marhey: 'Marhey', ruqaa: "'Aref Ruqaa'", vibes: 'Vibes' })[f] || 'Lalezar'; };

  // مسار بنقاط مفتاحية: [a,b,c] يُستوفى بالتساوي خلال 0..1 (ناعم)
  const kf = (arr, q) => { if (!arr || !arr.length) return null; if (arr.length === 1) return arr[0];
    const f = clamp(q) * (arr.length - 1), i = Math.min(arr.length - 2, Math.floor(f)), u = f - i; return arr[i] + (arr[i + 1] - arr[i]) * sm(u); };
  const seqAt = (list, s, t) => { const a = (list || 'happy').split('>'); const k = Math.min(a.length - 1, Math.floor(clamp((t - s.start) / (s.end - s.start), 0, 0.9999) * a.length)); return a[k]; };

  function draw(R, t, s) {
    if (R.turb) R.turb.setAttribute('seed', String(1 + (Math.floor(t * 10) % 6)));   // اهتزاز الخط ~10 مرات/ثانية
    const prog = clamp((t - s.start) / Math.max(0.1, s.end - s.start));
    // الرسومات: خط بعد خط ثم اللون
    R.draws.forEach(o => {
      const dur = 0.9 * (o.w.speed || 1), p = o.w.instant ? 1 : clamp((t - o.at) / dur), n = o.paths.length;   // = : موجودة من قبل، تظهر فوراً
      const sc = (o.w.s || 1) * (o.w.grow ? (0.2 + 0.8 * eoc(clamp((t - o.at) / (dur * 1.6)))) : 1);
      const fall = o.w.icon === 'drops' ? ` translate(0 ${(((t * 1.4) % 1) * 70).toFixed(1)})` : '';   // قطرات تنزل باستمرار
      const wig = o.w.wiggle ? ` rotate(${(Math.sin(t * 40) * 12).toFixed(1)}) translate(${(Math.sin(t * 55) * 6).toFixed(1)} 0)` : '';   // ! : اهتزاز (منبّه يرن)
      o.g.setAttribute('transform', `translate(${o.w.x} ${o.w.y}) scale(${sc.toFixed(3)})${wig}${fall}`);
      if (o.w.icon === 'drops') o.g.setAttribute('opacity', (1 - ((t * 1.4) % 1) * 0.6).toFixed(2));
      o.paths.forEach((pth, k) => { const q = clamp(p * n - k); pth.style.strokeDashoffset = String(1 - q);
        const f = pth.dataset.fill; pth.style.fillOpacity = f === 'none' ? 0 : clamp((p - 0.75) / 0.25); });
    });
    // الشخصيات
    let headPos = null;
    if (R.d.fish && R.chars[0]) R.chars[0].c._bend = ({ fight: 1, jump: 0.45, bite: 0.5 })[R.d.fish.mode] || 0;
    R.chars.forEach((o, k) => {
      const c = o.c, x0 = c.x0 != null ? c.x0 : 540, x1 = c.x1 != null ? c.x1 : x0;
      const mv = Math.abs(x1 - x0) > 2, q = mv ? eoc(clamp(prog / (c.walkEnd || 0.85))) : 0;
      const pq = clamp(prog / (c.walkEnd || 1));   // تقدّم المسار (للصعود والسقوط والدوران)
      const x = c.xs ? kf(c.xs, pq) : x0 + (x1 - x0) * q;
      const moving = mv && q < 0.999 && !c.ys;
      const fk = seqAt(c.face, s, t), pk = seqAt(c.pose, s, t);
      const dir = c.dir != null ? c.dir : (x1 < x0 ? -1 : 1), big = c.big || 1;
      const y = c.ys ? kf(c.ys, pq) : (c.y != null ? c.y : R.ground);
      const rv = c.rots ? kf(c.rots, pq) : (c.rot || 0);
      const rot = rv ? ` rotate(${rv.toFixed(1)})` : '';   // rot=-90 : مستلقٍ (حول القدمين)
      let sv = c.spins ? kf(c.spins, pq) : 0, ty = y;   // spin=0>720 : دوران حول منتصف الجسم
      let pivot = -200 * big;
      if (pk === 'curl') {
        // تدحرج فيزيائي: الجسم الملتف كرة نصف قطرها BALL_R، حافتها تلامس خط y دائماً (الأرض أو الكيس)،
        // والدوران يساوي المسافة المقطوعة ÷ نصف القطر (بلا انزلاق). y هنا = خط التلامس.
        const r = BALL_R * big, x0r = c.xs ? c.xs[0] : x0;
        pivot = -BALL_C * big; ty = y - r + BALL_C * big;
        if (!c.spins || c.spin === 'auto') sv = ((x - x0r) / r) * 180 / Math.PI * (dir < 0 ? -1 : 1);
      }
      const spin = sv ? ` rotate(${sv.toFixed(1)} 0 ${pivot.toFixed(0)})` : '';
      o.g.setAttribute('transform', `translate(${x.toFixed(1)} ${ty.toFixed(1)})${rot}${spin} scale(${(dir * big).toFixed(2)} ${big})`);
      const r = c.kind === 'dragon' ? dragonSVG(c, t + k * 0.37, fk, pk, prog) : charSVG(c, t + k * 0.37, fk, pk, moving, prog);
      o.g.innerHTML = r.svg;
      if (k === 0) R.tipW = r.tip ? { x: x + dir * big * r.tip.x, y: ty + big * r.tip.y } : null;
      // الرمي: بعد لحظة الإفلات يطير الشيء في قوس نحو الهدف
      if (pk === 'throw' && c.hold && ICONS[c.hold]) {
        if (!o.fly) { o.fly = document.createElementNS(NS, 'g'); R.svg.querySelector('.front').appendChild(o.fly); o.fly.innerHTML = ICONS[c.hold](INK[c.ink] || INK.pencil); }
        const rel = releaseHand(c), sx = x + dir * big * rel.x, sy = y + big * rel.y;
        const [tx, ty] = (c.to || '').split(',').map(Number);
        const ex = isFinite(tx) ? tx : sx + dir * 520, ey = isFinite(ty) ? ty : y - 60;
        const q = clamp((prog - 0.5) / 0.4);
        o.fly.setAttribute('opacity', prog < 0.5 ? 0 : 1);
        const fx2 = sx + (ex - sx) * q, fy2 = sy + (ey - sy) * q - Math.sin(q * Math.PI) * 320;
        o.fly.setAttribute('transform', `translate(${fx2.toFixed(1)} ${fy2.toFixed(1)}) rotate(${(q * 540 * dir).toFixed(0)}) scale(${((c.hold_s || 0.45) * big).toFixed(2)})`);
      } else if (o.fly) o.fly.setAttribute('opacity', 0);
      if (k === 0) headPos = c.rot ? { x: x + Math.sin(-c.rot * D2R) * -335 * big, y: y - Math.cos(c.rot * D2R) * 335 * big } : { x, y: y - 335 * big };
    });
    // الكيس الهوائي ينضغط حين تهبط عليه الشخصية ثم يرتد (يُحسب من موضع القدمين)
    if (R.chars.length) R.draws.forEach(o => {
      if (o.w.icon !== 'airbag') return;
      const sc = o.w.s || 1, top = o.w.y - 150 * sc, ch = R.chars[0].g.transform.baseVal.consolidate();
      if (!ch) return;
      const fy = ch.matrix.f, fx = ch.matrix.e, near = Math.abs(fx - o.w.x) < 230 * sc;
      const sq = near ? clamp(1 - Math.abs(fy - (top + 70 * sc)) / (90 * sc)) * 0.28 : 0;
      const base = o.w.y + 85 * sc;
      o.g.setAttribute('transform', `translate(${o.w.x} ${base}) scale(${(sc * (1 + sq * 0.55)).toFixed(3)} ${(sc * (1 - sq)).toFixed(3)}) translate(0 ${-85})`);
    });
    drawBall(R, t, s);
    drawFishing(R, t, s, R.tipW);
    drawClassExtras(R, t, s, headPos);
    // فقاعة التفكير تظهر ثم تنفجر
    if (R.think && headPos) {
      const a = s.start + 0.35, e = s.end - 0.35, pin = eob(clamp((t - a) / 0.35)), pop = clamp((t - e) / 0.3);
      const sc = pop > 0 ? 1 + pop * 0.5 : 0.2 + 0.8 * pin;
      R.think.setAttribute('transform', `translate(${Math.min(780, Math.max(300, headPos.x + 170))} ${headPos.y - 300}) scale(${sc.toFixed(3)})`);
      R.think.setAttribute('opacity', t < a ? 0 : (1 - pop).toFixed(3));
    }
    // فقاعة الكلام فوق الرأس
    if (R.say && headPos) {
      const a = s.start + (R.d.say_at || 0.3), p = eob(clamp((t - a) / 0.3));
      const w = R.say.offsetWidth, bx = Math.min(1080 - w - 30, Math.max(30, headPos.x - w / 2)), by = headPos.y - 230;
      R.say.style.opacity = t < a ? 0 : 1;
      R.say.style.transform = `translate(${bx}px,${by}px) scale(${(0.3 + 0.7 * p).toFixed(3)})`;
    }
  }

  /* ---------------- الكرة الفيزيائية (ball= في المشاهد) ----------------
     محاكاة واحدة متصلة عبر كل المشاهد (الكرة تبقى حيث توقفت): جاذبية، ارتداد عن الأرض، تدحرج باحتكاك
     ودوران = المسافة ÷ نصف القطر، ارتطام برأس الشخصية (bonk=1)، وشبكة المرمى (goal) تمتص الكرة وتنتفخ. */
  const BG = 2600, DT = 1 / 240;
  let BS = null;
  function ballEvents() {
    const TL = window.TIMELINE, ev = [];
    TL.scenes.forEach(s => { const b = s.doodle && s.doodle.ball; if (!b) return;
      const T = f => s.start + f * (s.end - s.start);
      if (b.kick) ev.push({ t: T(b.kick[0]), v: [b.kick[1], b.kick[2]] });
      if (b.set) ev.push({ t: s.start, p: b.set });
      if (b.x != null && !ev.length) ev.push({ t: 0, p: [b.x, null, 0, 0], r: b.r });
    });
    return ev.sort((a, b) => a.t - b.t);
  }
  function sceneAt(t) { const S = window.TIMELINE.scenes; for (let i = S.length - 1; i >= 0; i--) if (t >= S[i].start) return S[i]; return S[0]; }
  function ballState(t) {
    if (!BS || t < BS.t - 1e-9) { const ev = ballEvents(); const e0 = ev.find(e => e.p) || { p: [540, null, 0, 0] };
      BS = { t: 0, x: e0.p[0], y: null, vx: 0, vy: 0, a: 0, r: (ev.find(e => e.r) || {}).r || 42, ev, k: 0, net: -9, air: false, hit: -9 }; }
    while (BS.t < t) {
      const s = sceneAt(BS.t), d = s.doodle || {}, gy = d.ground != null ? d.ground : 1560, r = BS.r;
      while (BS.k < BS.ev.length && BS.ev[BS.k].t <= BS.t) { const e = BS.ev[BS.k++];
        if (e.p) { BS.x = e.p[0]; BS.y = e.p[1]; BS.vx = e.p[2] || 0; BS.vy = e.p[3] || 0; }
        if (e.v) { BS.vx = e.v[0]; BS.vy = e.v[1]; BS.hit = BS.t; } }
      if (BS.y == null) BS.y = gy - r;
      const onG = BS.y >= gy - r - 0.5 && Math.abs(BS.vy) < 1;
      if (!onG) BS.vy += BG * DT;
      BS.px = BS.x; BS.x += BS.vx * DT; BS.y += BS.vy * DT;
      if (BS.y > gy - r) { BS.y = gy - r; BS.vy = Math.abs(BS.vy) > 260 ? -BS.vy * 0.5 : 0; if (BS.vy) BS.hit = BS.t; }
      if (BS.y >= gy - r - 0.5 && !BS.vy) { const dec = 520 * DT; BS.vx = Math.abs(BS.vx) <= dec ? 0 : BS.vx - Math.sign(BS.vx) * dec; BS.a += BS.vx * DT / r; }
      else BS.a += BS.vx * DT / r * 0.6;
      // المرمى: الشبكة الخلفية مائلة من (gx+170, أعلى) إلى (gx+230, الأرض)
      (d.draws || []).forEach(w => { if (w.icon !== 'goal') return; const sc = w.s || 1, gx = w.x, top = gy - 330 * sc;
        // سقف المرمى (الشبكة العلوية): الكرة النازلة من فوق ترتد عنه ولا تدخل
        if (BS.vy > 0 && BS.x > gx - r * 0.5 && BS.x < gx + 175 * sc && BS.y + r > top - 6 && BS.y < top) { BS.y = top - 6 - r; BS.vy = -BS.vy * 0.45; BS.vx += 160; }
        else if (BS.x > gx && BS.y > top) { const wx = gx + (170 + 60 * (BS.y - top) / (gy - top)) * sc;
          if (BS.x + r > wx && BS.vx > 0 && BS.px + r <= wx + 2) { BS.x = wx - r; BS.vx = -BS.vx * 0.04; BS.net = BS.t; } } });
      // ارتطام برأس الشخصية الأولى
      if (d.ball && d.ball.bonk && d.chars && d.chars[0] && BS.t < s.start + (d.ball.bonk_until != null ? d.ball.bonk_until : 1) * (s.end - s.start)) { const c = d.chars[0], big = c.big || 1, hx = c.x1 != null ? c.x1 : (c.x0 || 540), hy = (c.y != null ? c.y : gy) - 335 * big, R = 70 * big;
        const dx = BS.x - hx, dy = BS.y - hy, dist = Math.hypot(dx, dy);
        if (dist < R + r) { const nx = dx / dist, ny = dy / dist, vn = BS.vx * nx + BS.vy * ny;
          if (vn < 0) { BS.vx -= 1.55 * vn * nx; BS.vy -= 1.55 * vn * ny; BS.x = hx + nx * (R + r); BS.y = hy + ny * (R + r); BS.bonk = BS.t; } } }
      BS.t += DT;
    }
    if (BS.y == null) { const d = sceneAt(t).doodle || {}; BS.y = (d.ground != null ? d.ground : 1560) - BS.r; }
    return BS;
  }
  // كرة قدم واقعية: بيضاء بخماسيات سوداء (نمط تيلستار)، ظل كروي وخطوط خياطة، ولمعة ثابتة لا تدور
  function soccerBall(r, u) {
    const pent = (cx, cy, rr, rot) => 'M' + [0, 1, 2, 3, 4].map(k => { const a = (rot + k * 72 - 90) * D2R; return `${(cx + Math.cos(a) * rr).toFixed(1)} ${(cy + Math.sin(a) * rr).toFixed(1)}`; }).join(' L') + 'Z';
    const pr = r * 0.34, outer = [0, 1, 2, 3, 4].map(k => { const a = (k * 72 + 36 - 90) * D2R; return [Math.cos(a) * r * 0.9, Math.sin(a) * r * 0.9, k * 72 + 36]; });
    const vtx = [0, 1, 2, 3, 4].map(k => { const a = (k * 72 - 90) * D2R; return [Math.cos(a) * pr, Math.sin(a) * pr, Math.cos(a) * r * 1.05, Math.sin(a) * r * 1.05]; });
    return `<defs><radialGradient id="bs${u}" cx="38%" cy="32%" r="75%"><stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#eef0f2"/><stop offset="1" stop-color="#9aa1a8"/></radialGradient>
      <clipPath id="bc${u}"><circle r="${r}"/></clipPath></defs>
      <circle r="${r}" fill="url(#bs${u})"/>
      <g clip-path="url(#bc${u})">
        <path d="${pent(0, 0, pr, 0)}" fill="#1b1b1b"/>
        ${outer.map(([x, y, rot]) => `<path d="${pent(x, y, pr * 1.05, rot + 180)}" fill="#1b1b1b"/>`).join('')}
        <path d="${vtx.map(([x, y, X, Y]) => `M${x.toFixed(1)} ${y.toFixed(1)} L${X.toFixed(1)} ${Y.toFixed(1)}`).join(' ')}" stroke="#6c737a" stroke-width="2.2" fill="none"/>
        <circle r="${r}" fill="none" stroke="rgba(0,0,0,.18)" stroke-width="${(r * 0.25).toFixed(1)}" transform="translate(${(r * 0.08).toFixed(1)} ${(r * 0.1).toFixed(1)})"/>
      </g>
      <circle r="${r}" fill="none" stroke="#1b1b1b" stroke-width="3.5"/>`;
  }
  function drawBall(R, t, s) {
    if (!window.TIMELINE.scenes.some(x => x.doodle && x.doodle.ball)) return;
    if (!R.ball) { R.ball = document.createElementNS(NS, 'g'); R.svg.querySelector('.front').appendChild(R.ball); }
    let b = ballState(t); const ink = INK[R.d.ink] || INK.pencil;
    const sh = R.d.ball && R.d.ball.shot;
    if (sh) {   // لقطة إعادة أمامية: الكرة تبتعد عن الكاميرا نحو نقطة في المرمى (تصغر)، ثم ترتج الشبكة وتسقط
      const [x0, y0, x1, y1, r0, r1, a, e] = sh, T = f => s.start + f * (s.end - s.start);
      const q = clamp((t - T(a)) / Math.max(0.05, T(e) - T(a))), k = 1 - Math.pow(1 - q, 2.2);
      const fall = Math.max(0, t - T(e)), gy = R.d.ball.floor || y1, yy = Math.min(gy, y1 + 0.5 * 2600 * 0.35 * fall * fall);
      b = { x: x0 + (x1 - x0) * k, y: q < 1 ? y0 + (y1 - y0) * k - Math.sin(q * Math.PI) * 120 : yy, vx: q < 1 ? 2000 : 0, vy: q < 1 ? -400 : 0,
            a: q * 9, r: r0 + (r1 - r0) * k, net: q >= 1 ? T(e) : -9, bonk: -9 };
      R.d.shotNet = q >= 1 ? T(e) : -9;
      R.draws.forEach(o => { if (o.w.icon !== 'goalfront') return; const net = o.g.querySelector('.net'); if (!net) return;
        const kk = t - T(e), amp = kk >= 0 && kk < 1.2 ? Math.sin(kk * 16) * Math.exp(-kk * 3.5) : 0;
        const cx = (x1 - o.w.x) / (o.w.s || 1), cy = (y1 - o.w.y) / (o.w.s || 1);
        net.setAttribute('transform', `translate(${cx} ${cy}) scale(${(1 + amp * 0.06).toFixed(3)}) translate(${-cx} ${-cy})`); });
    }
    const r = b.r;
    R.ball.setAttribute('transform', `translate(${b.x.toFixed(1)} ${b.y.toFixed(1)}) rotate(${(b.a * 180 / Math.PI).toFixed(1)})`);
    const fast = Math.hypot(b.vx, b.vy) > 900, ang = Math.atan2(b.vy, b.vx);
    R.ball.innerHTML = soccerBall(r, R.uid || (R.uid = ++UID));
    if (!R.gloss) { R.gloss = document.createElementNS(NS, 'g'); R.svg.querySelector('.front').appendChild(R.gloss); }
    R.gloss.innerHTML = `<ellipse cx="${(b.x - r * 0.38).toFixed(1)}" cy="${(b.y - r * 0.42).toFixed(1)}" rx="${(r * 0.26).toFixed(1)}" ry="${(r * 0.15).toFixed(1)}" fill="#fff" opacity=".75" transform="rotate(-35 ${(b.x - r * 0.38).toFixed(1)} ${(b.y - r * 0.42).toFixed(1)})"/>`;
    // خطوط سرعة خلف الكرة السريعة (لا تدور معها)
    if (!R.trail) { R.trail = document.createElementNS(NS, 'g'); R.svg.querySelector('.front').insertBefore(R.trail, R.ball); }
    R.trail.innerHTML = fast ? [0, -1, 1].map(k => `<path d="M${(b.x - Math.cos(ang) * (r + 20) + k * Math.sin(ang) * 22).toFixed(1)} ${(b.y - Math.sin(ang) * (r + 20) - k * Math.cos(ang) * 22).toFixed(1)} l${(-Math.cos(ang) * (110 - Math.abs(k) * 35)).toFixed(1)} ${(-Math.sin(ang) * (110 - Math.abs(k) * 35)).toFixed(1)}" stroke="${ink}" stroke-width="6" stroke-linecap="round" opacity=".7"/>`).join('') : '';
    // انتفاخ الشبكة وارتجافها عند الهدف
    R.draws.forEach(o => { if (o.w.icon !== 'goal') return; const k = t - b.net;
      const net = o.g.querySelector('.net'); if (!net) return;
      const bul = k >= 0 && k < 0.9 ? Math.sin(k * 18) * Math.exp(-k * 4) * 26 : 0; net.setAttribute('transform', `translate(${bul.toFixed(1)} 0)`); });
    // نجوم الدوار بعد الارتطام بالرأس
    const kb = t - (b.bonk || -9);
    if (!R.dizzy) { R.dizzy = document.createElementNS(NS, 'g'); R.svg.querySelector('.front').appendChild(R.dizzy); }
    if (kb >= 0 && kb < 2.2 && R.d.chars && R.d.chars[0]) { const c = R.d.chars[0], big = c.big || 1, hx = c.x1 != null ? c.x1 : c.x0, hy = (c.y != null ? c.y : R.ground) - 335 * big - 90 * big;
      R.dizzy.innerHTML = [0, 1, 2].map(i => { const a2 = t * 5 + i * 2.1; return `<path transform="translate(${(hx + Math.cos(a2) * 110).toFixed(1)} ${(hy + Math.sin(a2) * 26).toFixed(1)}) scale(.5)" d="M0 -30 L9 -9 L30 -9 L13 5 L19 28 L0 14 L-19 28 L-13 5 L-30 -9 L-9 -9Z" fill="#ffd43b" stroke="${ink}" stroke-width="5"/>`; }).join('');
    } else R.dizzy.innerHTML = '';
  }

  /* ---------------- الصيد: سطح الماء، الصنارة والخيط والعوّامة والخطاف، والسمك (fish= / fishes= / water=) ---------------- */
  function fishSVG(kind, s, t, ink, hooked) {
    const w = Math.sin(t * (hooked ? 22 : 9)) * (hooked ? 22 : 12);
    if (kind === 'big') return `<g transform="scale(${s})"><path d="M-70 0 L-118 ${-30 + w} L-112 ${30 + w}Z" fill="#ff8c42" stroke="#b34a00" stroke-width="5" stroke-linejoin="round"/>
      <path d="M-80 0 C-60 -52 50 -56 82 -6 C70 30 -40 50 -80 0Z" fill="#ff8c42" stroke="#b34a00" stroke-width="6"/>
      <path d="M-10 -40 C0 -62 30 -60 38 -44" fill="#ffb37a" stroke="#b34a00" stroke-width="4"/><path d="M-20 10 C-6 26 10 26 16 14" fill="none" stroke="#b34a00" stroke-width="4"/>
      <path d="M-40 -20 q10 20 0 40 M-25 -26 q12 26 0 52" stroke="#b34a00" stroke-width="3" fill="none" opacity=".6"/>
      <circle cx="52" cy="-14" r="11" fill="#fff" stroke="#1b1b1b" stroke-width="3"/><circle cx="55" cy="-14" r="5" fill="#1b1b1b"/>
      <path d="M78 6 q6 3 0 8" stroke="#b34a00" stroke-width="4" fill="none"/></g>`;
    return `<g transform="scale(${s})"><path d="M-40 0 L-66 ${-18 + w} L-62 ${18 + w}Z" fill="none" stroke="${ink}" stroke-width="5" stroke-linejoin="round"/>
      <path d="M-44 0 C-30 -30 30 -32 46 -4 C36 18 -24 28 -44 0Z" fill="#eaf4fa" stroke="${ink}" stroke-width="5"/><circle cx="28" cy="-8" r="4" fill="${ink}"/></g>`;
  }
  function fishPos(f, R, t, s) {
    const q = clamp((t - s.start) / Math.max(0.1, s.end - s.start));
    const x = f.xs ? kf(f.xs, q) : f.x, y = f.ys ? kf(f.ys, q) : f.y;
    const q2 = clamp(q + 0.01), x2 = f.xs ? kf(f.xs, q2) : x, y2 = f.ys ? kf(f.ys, q2) : y;
    const dir = f.dir != null ? f.dir : (x2 < x - 0.01 ? -1 : 1);
    const ang = f.ys ? Math.atan2(y2 - y, Math.abs(x2 - x) + 1e-3) * 180 / Math.PI * (Math.abs(y2 - y) > 2 ? 1 : 0) : 0;
    return { x, y, dir, ang: clamp(ang, -70, 70) * (f.tilt === 0 ? 0 : 1), mouth: { x: x + dir * 80 * (f.s || 1), y: y + 6 * (f.s || 1) } };
  }
  function drawFishing(R, t, s, tipW) {
    const d = R.d, W = d.water; if (W == null) return;
    const ink = INK[d.ink] || INK.pencil, prog = clamp((t - s.start) / Math.max(0.1, s.end - s.start)), T = f => s.start + f * (s.end - s.start);
    if (!R.wat) { R.wat = document.createElementNS(NS, 'g'); R.svg.querySelector('.draws').prepend(R.wat); R.fl = document.createElementNS(NS, 'g'); R.svg.querySelector('.front').appendChild(R.fl); }
    // سطح الماء المتموّج + خطوط ضوء تحت الماء + فقاعات
    let wave = `M0 ${W}`; for (let x = 0; x <= 1080; x += 30) wave += ` L${x} ${(W + Math.sin(x / 70 + t * 1.8) * 6 + Math.sin(x / 31 - t * 2.6) * 2).toFixed(1)}`;
    let caus = ''; for (let k = 0; k < 7; k++) { const y = W + 120 + k * 120, o = Math.sin(t * 1.2 + k) * 30; caus += `<path d="M${60 + k * 37 + o} ${y} q60 -14 120 0 t120 0" stroke="#ffffff" stroke-width="5" fill="none" opacity=".35"/>`; }
    let bub = ''; for (let k = 0; k < 9; k++) { const ph = ((t * 0.18 + k * 0.137) % 1), bx = 120 + ((k * 263) % 860) + Math.sin(t * 2 + k) * 10, by = 1900 - ph * (1900 - W - 20); bub += `<circle cx="${bx.toFixed(1)}" cy="${by.toFixed(1)}" r="${4 + (k % 3) * 3}" fill="none" stroke="#fff" stroke-width="3" opacity="${(0.7 * (1 - ph)).toFixed(2)}"/>`; }
    R.wat.innerHTML = `${caus}${bub}<path d="${wave}" stroke="${ink}" stroke-width="5" fill="none" stroke-linecap="round"/>`;
    // السمك
    let fishSvg = '', hooked = null;
    (d.fishes || []).forEach((f, i) => { const p = fishPos(f, R, t, s); if (f.hooked) hooked = p;
      fishSvg += `<g transform="translate(${p.x.toFixed(1)} ${p.y.toFixed(1)}) scale(${p.dir} 1) rotate(${(p.ang * p.dir).toFixed(1)})">${fishSVG(f.kind, f.s || 1, t + i * 0.7, ink, f.hooked)}</g>`;
      if (Math.abs(p.y - W) < 70 && f.ys) { const k2 = 1 - Math.abs(p.y - W) / 70;   // رذاذ عند عبور السطح
        fishSvg += [0, 1, 2, 3, 4, 5].map(j => { const a = (-150 + j * 24) * D2R, r = 50 + 70 * k2; return `<path d="M${(p.x + Math.cos(a) * r * 0.6).toFixed(1)} ${(W + Math.sin(a) * r * 0.9).toFixed(1)} q6 -14 0 -22 q-6 8 0 22Z" fill="#9cc9e4" stroke="${ink}" stroke-width="3" opacity="${k2.toFixed(2)}"/>`; }).join(''); } });
    // العوّامة والخطاف والخيط
    const F = d.fish || {}; let out = fishSvg;
    if (tipW && F.mode) {
      const fx = F.x || 800, depth = F.depth || W + 380, a = T(F.at != null ? F.at : 0.3);
      let fl = { x: fx, y: W + Math.sin(t * 2.2) * 5 }, hook = { x: fx, y: depth + Math.sin(t * 1.7) * 6 }, slack = 1, show = true, rip = null, under = true;
      const dangle = { x: tipW.x + 30, y: tipW.y + 120 };
      if (F.mode === 'cast') {
        if (t < a) { fl = dangle; hook = { x: dangle.x, y: dangle.y + 70 }; under = false; }
        else { const q = clamp((t - a) / 0.7), qq = 1 - Math.pow(1 - q, 1.6);
          if (q < 1) { fl = { x: dangle.x + (fx - dangle.x) * qq, y: dangle.y + (W - dangle.y) * q - Math.sin(q * Math.PI) * 260 }; hook = { x: fl.x, y: fl.y + 70 }; under = false; }
          else { const k = clamp((t - a - 0.7) / 1.3); hook = { x: fx, y: W + 70 + (depth - W - 70) * (1 - Math.pow(1 - k, 2)) }; rip = a + 0.7; } }
      }
      if (F.mode === 'nibble') (F.dips || [0.3, 0.5, 0.72]).forEach(dp => { const k = t - T(dp); if (k > 0 && k < 0.6) { fl.y += Math.sin(k / 0.6 * Math.PI) * 22; hook.x += Math.sin(k * 40) * 6; rip = T(dp); } });
      if (F.mode === 'bite') { const k = clamp((t - a) / 0.35); fl.y += k * 140; rip = a; slack = 1 - k; hook = hooked ? hooked.mouth : hook; }
      if (F.mode === 'yank') { const k = clamp((t - a) / 0.35), k2 = 1 - Math.pow(1 - k, 2);
        if (k > 0) { fl = { x: fx + (dangle.x - fx) * k2, y: W + (dangle.y - W) * k2 - Math.sin(k * Math.PI) * 120 }; hook = { x: fl.x, y: fl.y + 70 + (1 - k) * (depth - W - 70) }; rip = a; under = k < 0.3; } }
      if (F.mode === 'fight' || F.mode === 'jump') { hook = hooked ? hooked.mouth : hook; fl = null; slack = 0; }
      if (F.mode === 'none') show = false;
      if (show) {
        const end = fl || hook, mx = (tipW.x + end.x) / 2, my = (tipW.y + end.y) / 2 + 90 * slack;
        out += `<path d="M${tipW.x.toFixed(1)} ${tipW.y.toFixed(1)} Q${mx.toFixed(1)} ${my.toFixed(1)} ${end.x.toFixed(1)} ${end.y.toFixed(1)}" stroke="${ink}" stroke-width="2.5" fill="none" opacity=".85"/>`;
        if (fl) out += `<path d="M${fl.x.toFixed(1)} ${fl.y.toFixed(1)} L${hook.x.toFixed(1)} ${hook.y.toFixed(1)}" stroke="${ink}" stroke-width="2" fill="none" opacity=".7"/>
          <g transform="translate(${fl.x.toFixed(1)} ${fl.y.toFixed(1)})"><path d="M0 -26 V-40" stroke="${ink}" stroke-width="4"/><path d="M-14 -4 A14 14 0 0 1 14 -4 L14 -14 A14 14 0 0 0 -14 -14Z" fill="#e63946"/><circle r="15" cy="-10" fill="none" stroke="${ink}" stroke-width="4"/><path d="M-14 -8 h28" stroke="${ink}" stroke-width="3"/><path d="M-14 -8 A14 14 0 0 0 14 -8" fill="#fff" stroke="${ink}" stroke-width="3"/></g>`;
        if (!hooked || (F.mode !== 'fight' && F.mode !== 'jump' && F.mode !== 'bite')) out += `<g transform="translate(${hook.x.toFixed(1)} ${hook.y.toFixed(1)})"><path d="M0 0 V22 Q0 36 -12 32 Q-20 26 -16 18" stroke="${ink}" stroke-width="4" fill="none"/>${F.worm === 0 ? '' : `<path d="M-2 14 q${(8 + Math.sin(t * 9) * 5).toFixed(1)} 8 0 16 q-8 6 0 14" stroke="#d6336c" stroke-width="7" fill="none" stroke-linecap="round"/>`}</g>`;
      }
      if (rip != null && t >= rip) { const k = t - rip; out += [0, 0.35, 0.7].map(o => { const kk = k - o; if (kk < 0 || kk > 1.6) return ''; return `<ellipse cx="${fx}" cy="${W + 4}" rx="${(20 + kk * 90).toFixed(1)}" ry="${(6 + kk * 22).toFixed(1)}" fill="none" stroke="${ink}" stroke-width="3" opacity="${(0.8 * (1 - kk / 1.6)).toFixed(2)}"/>`; }).join(''); }
    }
    R.fl.innerHTML = out;
  }

  /* ---------------- ساعة حائط بعقارب تدور (clock=x,y,s,سرعة) وفقاعة حلم ملوّنة متحركة (dream=x,y,s,pop) ---------------- */
  function drawClassExtras(R, t, s, headPos) {
    const d = R.d, ink = INK[d.ink] || INK.pencil;
    if (!R.cx) { R.cx = document.createElementNS(NS, 'g'); R.svg.querySelector('.draws').appendChild(R.cx); R.dr = document.createElementNS(NS, 'g'); R.svg.querySelector('.think').appendChild(R.dr); }
    let out = '';
    if (d.clock) { const [x, y, sc, sp] = d.clock, m = t * (sp || 0.02) * 360, h = m / 12;
      out += `<g transform="translate(${x} ${y}) scale(${sc || 1})"><circle r="62" fill="#fff" stroke="${ink}" stroke-width="7"/>${[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map(k => `<path d="M0 -52 V${k % 3 ? -46 : -40}" transform="rotate(${k * 30})" stroke="${ink}" stroke-width="${k % 3 ? 3 : 5}"/>`).join('')}
        <path d="M0 0 V-30" transform="rotate(${(h + 300).toFixed(1)})" stroke="${ink}" stroke-width="7" stroke-linecap="round"/><path d="M0 0 V-46" transform="rotate(${m.toFixed(1)})" stroke="${ink}" stroke-width="4" stroke-linecap="round"/><circle r="5" fill="${ink}"/></g>`; }
    R.cx.innerHTML = out;
    let dr = '';
    if (d.dream) { const [x, y, sc, popF] = d.dream, T = f => s.start + f * (s.end - s.start);
      const a = s.start + (d.dream_in != null ? d.dream_in : 0.3), pin = eob(clamp((t - a) / 0.5)), pop = popF ? clamp((t - T(popF)) / 0.25) : 0;
      if (t >= a && pop < 1) {
        const u = R.uid || (R.uid = ++UID), cyc = (t * 0.55) % 1, kx = clamp((cyc - 0.47) / 0.3), bx = -120 + 330 * kx, by = 40 - Math.sin(kx * Math.PI) * 70 - kx * 20;
        const mini = charSVG({ ink: '#3b3b3b', paper: '#ffffff' }, t, 'laugh', 'kick', false, cyc);
        dr = `<g transform="translate(${x} ${y}) scale(${(sc * (pop > 0 ? 1 + pop * 0.4 : 0.15 + 0.85 * pin)).toFixed(3)})" opacity="${(1 - pop).toFixed(2)}">
          <defs><clipPath id="dc${u}"><ellipse rx="300" ry="190"/></clipPath><linearGradient id="dg${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8fd3ff"/><stop offset=".62" stop-color="#d9f1ff"/><stop offset=".62" stop-color="#6cc46a"/><stop offset="1" stop-color="#3f9b46"/></linearGradient></defs>
          <g clip-path="url(#dc${u})"><rect x="-320" y="-200" width="640" height="400" fill="url(#dg${u})"/>
            <circle cx="200" cy="-120" r="34" fill="#ffd43b"/>${[-250, -200, -150, -100, -50, 0].map((cx2, k) => `<circle cx="${cx2}" cy="${-30 + (k % 2) * 8}" r="14" fill="${['#ff6b6b', '#ffd43b', '#4dabf7', '#f783ac', '#69db7c', '#ffa94d'][k]}" transform="translate(0 ${(Math.abs(Math.sin(t * 6 + k)) * -10).toFixed(1)})"/>`).join('')}
            <path d="M190 118 V-10 H270 L280 118" stroke="#fff" stroke-width="8" fill="none"/><path d="M200 0 L268 110 M230 -10 L276 100 M196 40 H272 M196 80 H276" stroke="#fff" stroke-width="2.5" opacity=".7"/>
            <g transform="translate(-170 118) scale(.55)">${mini.svg}</g>
            <g transform="translate(${bx.toFixed(1)} ${by.toFixed(1)}) rotate(${(kx * 500).toFixed(0)})">${soccerBall(16, u + 'd')}</g></g>
          <ellipse rx="300" ry="190" fill="none" stroke="${ink}" stroke-width="8"/></g>`;
        if (headPos) { const hx = headPos.x, hy = headPos.y; dr += [0.35, 0.6, 0.82].map((f, k) => `<circle cx="${(hx + (x - hx) * f * 0.6).toFixed(1)}" cy="${(hy + (y + 160 * sc - hy) * f).toFixed(1)}" r="${(10 + k * 7) * (1 - pop)}" fill="#fff" stroke="${ink}" stroke-width="4" opacity="${(pin * (1 - pop)).toFixed(2)}"/>`).join(''); }
        if (pop > 0) dr += [0, 1, 2, 3, 4, 5, 6, 7].map(k => { const an = k * 45 * D2R, r = 320 * sc * (1 + pop * 0.5); return `<path d="M${(x + Math.cos(an) * r).toFixed(1)} ${(y + Math.sin(an) * r * 0.65).toFixed(1)} l${(Math.cos(an) * 40).toFixed(1)} ${(Math.sin(an) * 30).toFixed(1)}" stroke="${ink}" stroke-width="6" opacity="${(1 - pop).toFixed(2)}"/>`; }).join('');
      }
    }
    R.dr.innerHTML = dr;
  }
  window.Doodle = { build, draw, ballState, ICONS: Object.keys(ICONS) };
})();
