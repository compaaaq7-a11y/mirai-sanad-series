/* salam-skill — محرك الرسوم الكرتونية المرسومة باليد (Doodle Cartoon)
   شخصية عصوية برأس كبير وتعابير مبالغ فيها، رسومات تُرسم خطاً خطاً، فقاعات تفكير وكلام، واهتزاز خط (line boil).
   كل شيء حتمي بالزمن t (لا CSS animations) حتى يعمل الرندر فريماً فريماً.
   الاستخدام من salam.html:  R.dd = Doodle.build(scene, camLayer, index);  Doodle.draw(R.dd, t, scene);  */
(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const eob = p => { const c1 = 1.7, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
  const eoc = p => 1 - Math.pow(1 - p, 3);
  const INK = { pencil: '#4a4a4a', blue: '#1f3fae', black: '#1b1b1b' };
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
      case 'sleep': return `<path d="M-36 -8 Q-24 2 -12 -8 M12 -8 Q24 2 36 -8" stroke="${ink}" stroke-width="5" fill="none"/><ellipse cy="30" rx="7" ry="${5 + Math.sin(t * 3) * 3}" fill="${ink}"/>`;
      case 'cry': { const y = 10 + ((t * 120) % 60); return face('sad', ink, t) + `<path d="M-26 ${y} q-6 10 0 14 q6 -4 0 -14Z M26 ${y} q-6 10 0 14 q6 -4 0 -14Z" fill="#3a86ff"/>`; }
      case 'wink': return `${dot(-24)}<path d="M12 -8 Q24 -20 36 -8" stroke="${ink}" stroke-width="5" fill="none"/><path d="M-24 18 Q0 40 24 18" stroke="${ink}" stroke-width="5" fill="none"/>`;
      case 'burnt': return `<circle cx="-24" cy="-8" r="9" fill="#fff"/><circle cx="24" cy="-8" r="9" fill="#fff"/>${blink ? '' : '<circle cx="-24" cy="-8" r="3" fill="#000"/><circle cx="24" cy="-8" r="3" fill="#000"/>'}`;
      default: return `${dot(-24)}${dot(24)}<path d="M-26 16 Q0 44 26 16" stroke="${ink}" stroke-width="5" fill="none"/>`; // happy
    }
  }

  /* ---------------- الوضعيات: زوايا الأطراف (درجات من الاتجاه للأسفل) ---------------- */
  function pose(kind, t, moving) {
    // aL/aR: [عضد، ساعد]، lL/lR: [فخذ، ساق]، lean: ميل الجذع، y: رفع الجسم، sway: إزاحة جانبية
    const P = { aL: [18, 8], aR: [-18, -8], lL: [8, 0], lR: [-8, 0], lean: 0, y: 0, sway: 0 };
    const w = Math.sin(t * (kind === 'run' ? 14 : 9));
    switch (kind) {
      case 'walk': case 'run': {
        const A = kind === 'run' ? 42 : 26;
        P.lL = [A * w, A * 0.5 * Math.max(0, -w) + 5]; P.lR = [-A * w, A * 0.5 * Math.max(0, w) + 5];
        P.aL = [-A * 0.9 * w + 10, -20]; P.aR = [A * 0.9 * w - 10, 20];
        P.y = -Math.abs(Math.cos(t * (kind === 'run' ? 14 : 9))) * (kind === 'run' ? 14 : 7); P.lean = kind === 'run' ? 12 : 3; break; }
      case 'jump': { const j = Math.abs(Math.sin(t * 5)); P.y = -j * 140; P.aL = [160, 10]; P.aR = [-160, -10]; P.lL = [25 - j * 10, -50 * (1 - j)]; P.lR = [-25 + j * 10, 50 * (1 - j)]; break; }
      case 'wave': P.aR = [-140 + Math.sin(t * 10) * 18, -30 + Math.sin(t * 10) * 25]; break;
      case 'cheer': P.aL = [150 + Math.sin(t * 12) * 15, 10]; P.aR = [-150 - Math.sin(t * 12) * 15, -10]; P.y = -Math.abs(Math.sin(t * 6)) * 30; break;
      case 'shiver': P.sway = Math.sin(t * 70) * 5; P.aL = [-35, -120]; P.aR = [35, 120]; P.lL = [3, 0]; P.lR = [-3, 0]; break;
      case 'bend': P.lean = 70; P.aL = [-10, 0]; P.aR = [-25, 0]; P.lL = [10, 0]; P.lR = [-5, 0]; break;
      case 'sit': P.y = 95; P.lL = [95, -90]; P.lR = [85, -80]; P.aL = [30, 40]; P.aR = [-20, -50]; break;
      case 'dance': { const d = Math.sin(t * 8); P.sway = d * 25; P.aL = [90 + d * 60, 40]; P.aR = [-90 + d * 60, -40]; P.lL = [15 + d * 15, 10]; P.lR = [-15 + d * 15, 10]; P.y = -Math.abs(d) * 12; P.lean = d * 8; break; }
      case 'think': P.aR = [-35, -150]; P.aL = [25, 70]; break;
      case 'point': P.aR = [95, -10]; P.aL = [15, 10]; break;   // الذراع للأمام باتجاه وجه الشخصية
    }
    if (moving && kind === 'stand') return pose('walk', t, true);
    return P;
  }

  function limb(x, y, a1, a2, L1, L2) {
    const x1 = x + Math.sin(a1 * D2R) * L1, y1 = y + Math.cos(a1 * D2R) * L1;
    const x2 = x1 + Math.sin((a1 + a2) * D2R) * L2, y2 = y1 + Math.cos((a1 + a2) * D2R) * L2;
    return `M${x} ${y} L${x1.toFixed(1)} ${y1.toFixed(1)} L${x2.toFixed(1)} ${y2.toFixed(1)}`;
  }

  function charSVG(c, t, faceKind, poseKind, moving) {
    const ink = INK[c.ink] || c.ink || INK.pencil;
    const P = pose(poseKind, t, moving);
    const burnt = faceKind === 'burnt', body = burnt ? '#111' : ink;
    const hipY = -120, neckY = -255, headY = -335, R = 70;
    // الجذع يميل حول الورك
    const lx = Math.sin(P.lean * D2R) * (hipY - neckY), ly = Math.cos(P.lean * D2R) * (hipY - neckY);
    const nx = lx, ny = hipY - ly, hx = Math.sin(P.lean * D2R) * (hipY - headY), hy = hipY - Math.cos(P.lean * D2R) * (hipY - headY);
    const shirt = c.shirt ? `<path d="M${nx - 28} ${ny + 8} L${-26} ${hipY + 6} L26 ${hipY + 6} L${nx + 28} ${ny + 8}Z" fill="${c.shirt}" stroke="${body}" stroke-width="7" stroke-linejoin="round"/>` : '';
    return `<g transform="translate(${P.sway} ${P.y})" stroke-linecap="round" stroke-linejoin="round">
      <path d="${limb(0, hipY, P.lL[0], P.lL[1], 62, 60)}" stroke="${body}" stroke-width="9" fill="none"/>
      <path d="${limb(0, hipY, P.lR[0], P.lR[1], 62, 60)}" stroke="${body}" stroke-width="9" fill="none"/>
      <path d="M0 ${hipY} L${nx.toFixed(1)} ${ny.toFixed(1)}" stroke="${body}" stroke-width="9"/>${shirt}
      ${c.scarf ? `<g transform="translate(${nx.toFixed(1)} ${(ny + 6).toFixed(1)})"><path d="M-46 -12 C-15 6 15 6 46 -12 L46 14 C15 30 -15 30 -46 14Z" fill="#e63946" stroke="#9d0208" stroke-width="5"/>
        <path d="M18 14 L${26 + Math.sin(t * 6) * 6} 80 L${46 + Math.sin(t * 6) * 6} 76 L38 10" fill="#e63946" stroke="#9d0208" stroke-width="5"/></g>` : ''}
      <path d="${limb(nx, ny + 15, P.aL[0], P.aL[1], 52, 50)}" stroke="${body}" stroke-width="8" fill="none"/>
      <path d="${limb(nx, ny + 15, P.aR[0], P.aR[1], 52, 50)}" stroke="${body}" stroke-width="8" fill="none"/>
      <g transform="translate(${hx.toFixed(1)} ${hy.toFixed(1)}) rotate(${P.lean * 0.4})">
        <circle r="${R}" fill="${burnt ? '#111' : '#fff'}" stroke="${body}" stroke-width="7"/>
        <path d="M-10 -68 q-6 -22 -2 -30 M4 -70 q2 -24 10 -30 M16 -66 q10 -16 20 -18" stroke="${body}" stroke-width="5" fill="none"/>
        ${face(faceKind, burnt ? '#fff' : ink, t)}
      </g></g>`;
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
    (d.chars || []).forEach(c => { const g = document.createElementNS(NS, 'g'); cg.appendChild(g); R.chars.push({ g, c }); });
    // فقاعة التفكير
    if (d.think && d.think.length && R.chars.length) {
      const g = document.createElementNS(NS, 'g'); svg.querySelector('.think').appendChild(g);
      const icons = d.think.map((n, k) => ICONS[n] ? `<g transform="translate(${(k - (d.think.length - 1) / 2) * 150} 0) scale(.62)">${ICONS[n](gink)}</g>` : '').join('');
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

  const seqAt = (list, s, t) => { const a = (list || 'happy').split('>'); const k = Math.min(a.length - 1, Math.floor(clamp((t - s.start) / (s.end - s.start), 0, 0.9999) * a.length)); return a[k]; };

  function draw(R, t, s) {
    if (R.turb) R.turb.setAttribute('seed', String(1 + (Math.floor(t * 10) % 6)));   // اهتزاز الخط ~10 مرات/ثانية
    const prog = clamp((t - s.start) / Math.max(0.1, s.end - s.start));
    // الرسومات: خط بعد خط ثم اللون
    R.draws.forEach(o => {
      const dur = 0.9 * (o.w.speed || 1), p = clamp((t - o.at) / dur), n = o.paths.length;
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
    R.chars.forEach((o, k) => {
      const c = o.c, x0 = c.x0 != null ? c.x0 : 540, x1 = c.x1 != null ? c.x1 : x0;
      const mv = Math.abs(x1 - x0) > 2, q = mv ? eoc(clamp(prog / (c.walkEnd || 0.85))) : 0, x = x0 + (x1 - x0) * q;
      const moving = mv && q < 0.999;
      const fk = seqAt(c.face, s, t), pk = seqAt(c.pose, s, t);
      const dir = c.dir != null ? c.dir : (x1 < x0 ? -1 : 1), big = c.big || 1, y = c.y != null ? c.y : R.ground;
      const rot = c.rot ? ` rotate(${c.rot})` : '';   // rot=-90 : مستلقٍ (في الفراش)
      o.g.setAttribute('transform', `translate(${x.toFixed(1)} ${y})${rot} scale(${(dir * big).toFixed(2)} ${big})`);
      o.g.innerHTML = charSVG(c, t + k * 0.37, fk, pk, moving);
      if (k === 0) headPos = c.rot ? { x: x + Math.sin(-c.rot * D2R) * -335 * big, y: y - Math.cos(c.rot * D2R) * 335 * big } : { x, y: y - 335 * big };
    });
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

  window.Doodle = { build, draw, ICONS: Object.keys(ICONS) };
})();
