// حلقة «كنز تحت الشجرة» — سند يحفر ليزرع فرعاً فيجد كنزاً، ميراي تقترح بيعه لمحل الذهب. بلا كلام ولا كتابة.
import { THREE, setup, rbox, gold, character, setFace, pose, walk, clamp, sm, lerp, eob, seg, rnd } from './lib.js';

const P = new URLSearchParams(location.search), W = +(P.get('w') || 540), H = +(P.get('h') || 960);
const { scene, cam, comp, sun } = setup(W, H);
const PI = Math.PI;
const V = (x, y, z) => new THREE.Vector3(x, y, z);

/* ------------------------------ الحقل والشجرة ------------------------------ */
const HOLE = { x: 1, z: -1 };
const field = new THREE.Group(); scene.add(field);
const R = rnd(7), tiles = {};
for (let x = -9; x <= 10; x++) for (let z = -9; z <= 5; z++) {
  const shade = ['#5fd35a', '#56c950', '#69dc62', '#4fbf4a'][Math.floor(R() * 4)];
  const m = rbox(1, 1, 1, shade, { r: 0.06, rough: 0.4 }); m.position.set(x, -0.5 + (R() < 0.1 ? 0.04 : 0), z); field.add(m); tiles[x + ',' + z] = m;
}
// طبقة تراب تحت مكان الحفرة (تظهر حين يُزال العشب)
const pit = new THREE.Group(); pit.position.set(HOLE.x, 0, HOLE.z); field.add(pit);
const pitWalls = []; for (const [dx, dz] of [[-0.5, 0], [0.5, 0], [0, -0.5], [0, 0.5]]) { const w = rbox(dx ? 0.08 : 1, 1.4, dz ? 0.08 : 1, '#6b4325', { r: 0.02 }); w.position.set(dx * 0.96, -0.7, dz * 0.96); pit.add(w); pitWalls.push(w); }
const pitFloor = rbox(0.96, 0.1, 0.96, '#5a371e', { r: 0.02 }); pit.add(pitFloor);
// الشجرة الكبيرة
const tree = new THREE.Group(); tree.position.set(-1.6, 0, -2.4); field.add(tree);
for (let y = 0; y < 4; y++) { const tr = rbox(0.9, 1, 0.9, y % 2 ? '#8b5a2b' : '#9a6634', { r: 0.06 }); tr.position.y = 0.5 + y; tree.add(tr); }
const LG = ['#2fb24a', '#3ccf5a', '#27a043', '#48d96a'];
const R2 = rnd(3);
for (let i = 0; i < 46; i++) { const s = 0.9 + R2() * 0.6, x = (R2() - 0.5) * 3.6, y = 4 + R2() * 2.4, z = (R2() - 0.5) * 3.2; if (x * x / 3.6 + (y - 5.1) * (y - 5.1) / 1.6 + z * z / 2.8 > 1.3) continue; const l = rbox(s, s, s, LG[i % 4], { r: 0.12, rough: 0.35 }); l.position.set(x, y, z); tree.add(l); }
for (let i = 0; i < 6; i++) { const a = rbox(0.28, 0.28, 0.28, '#ff4d4d', { rough: 0.2, metal: 0.1 }); a.position.set(-1.3 + R2() * 2.6, 3.9 + R2() * 1.6, 1.25 + R2() * 0.3); tree.add(a); }
// أزهار وشجيرات
const FL = ['#ff5fa2', '#ffd23f', '#7b61ff', '#ff8c42', '#3ec1ff'];
for (let i = 0; i < 26; i++) { const x = Math.round((R() - 0.5) * 18), z = -8 + Math.round(R() * 12); if (Math.abs(x - HOLE.x) < 3 && Math.abs(z - HOLE.z) < 3) continue;
  const st = rbox(0.08, 0.35, 0.08, '#2f8f3a', { r: 0.02 }); st.position.set(x + 0.2, 0.17, z + 0.1); field.add(st);
  const f = rbox(0.24, 0.24, 0.24, FL[i % 5], { rough: 0.25 }); f.position.set(x + 0.2, 0.4, z + 0.1); field.add(f); }
for (let i = 0; i < 5; i++) { const b = rbox(1.1, 0.8, 1.1, '#37b54a', { r: 0.2 }); b.position.set(-8 + i * 4.2 + R() , 0.4, -8.2); field.add(b); }
// غيوم وشمس
const clouds = []; for (let i = 0; i < 5; i++) { const c = new THREE.Group(); for (let k = 0; k < 4; k++) { const b = rbox(1.6 + R(), 0.9, 1.2, '#ffffff', { r: 0.3, rough: 0.6, shadow: false }); b.position.set(k * 1.1 - 1.6, (k % 2) * 0.35, (R() - 0.5) * 0.6); c.add(b); } c.position.set(-14 + i * 7, 11 + R() * 3, -14 - R() * 6); scene.add(c); clouds.push(c); }
const sunB = rbox(2.2, 2.2, 0.4, '#ffe14d', { emissive: '#ffcc00', ei: 0.6, shadow: false }); sunB.position.set(9, 16, -22); scene.add(sunB);

/* ------------------------------ الأدوات ------------------------------ */
function sapling() { const g = new THREE.Group(); const st = rbox(0.09, 0.8, 0.09, '#7a4b24', { r: 0.03 }); st.position.y = 0.4; g.add(st);
  [[0.18, 0.62, 0], [-0.16, 0.74, 0.04], [0.02, 0.9, -0.05]].forEach(([x, y, z]) => { const l = rbox(0.28, 0.2, 0.2, '#47d65f', { r: 0.06 }); l.position.set(x, y, z); g.add(l); }); return g; }
const sap = sapling(); scene.add(sap);
const shovel = new THREE.Group(); { const h = rbox(0.09, 1.5, 0.09, '#a8683a', { r: 0.03 }); h.position.y = -0.2; shovel.add(h);
  const bl = rbox(0.42, 0.5, 0.06, '#c9d3dc', { metal: 0.9, rough: 0.2, r: 0.04 }); bl.position.y = -1.15; shovel.add(bl);
  const gr = rbox(0.3, 0.08, 0.08, '#333', { r: 0.03 }); gr.position.y = 0.55; shovel.add(gr); }
scene.add(shovel);
// صندوق الكنز
const chest = new THREE.Group(); scene.add(chest);
const cBase = rbox(1.1, 0.62, 0.76, '#a0522d', { rough: 0.45 }); cBase.position.y = 0.31; chest.add(cBase);
[-0.42, 0.42].forEach(x => { const b = new THREE.Mesh(cBase.geometry.clone().scale(0.11 / 1.1, 1.02, 1.03), gold()); b.position.set(x, 0.31, 0); chest.add(b); });
const lid = new THREE.Group(); lid.position.set(0, 0.62, -0.38); chest.add(lid);
const lidB = rbox(1.12, 0.3, 0.78, '#8b4513', { rough: 0.45, r: 0.12 }); lidB.position.set(0, 0.15, 0.38); lid.add(lidB);
[-0.42, 0.42].forEach(x => { const b = rbox(0.13, 0.32, 0.8, '#ffc93c', { metal: 1, rough: 0.2, emissive: '#ff9a00', ei: 0.2, r: 0.04 }); b.position.set(x, 0.15, 0.38); lid.add(b); });
const lock = rbox(0.2, 0.24, 0.08, '#ffc93c', { metal: 1, rough: 0.15, emissive: '#ff9a00', ei: 0.3, r: 0.04 }); lock.position.set(0, 0.6, 0.4); chest.add(lock);
const loot = new THREE.Group(); loot.position.y = 0.6; chest.add(loot);
const GM = gold({ ei: 0.2 });
const R3 = rnd(11);
for (let i = 0; i < 34; i++) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.03, 20), GM); c.position.set((R3() - 0.5) * 0.9, R3() * 0.12, (R3() - 0.5) * 0.55); c.rotation.set(R3() * 0.8, 0, R3() * 0.8); loot.add(c); }
['#ff3b6b', '#33d1ff', '#7cff6b', '#c77dff'].forEach((col, i) => { const g = new THREE.Mesh(new THREE.OctahedronGeometry(0.11), new THREE.MeshStandardMaterial({ color: col, metalness: 0.3, roughness: 0.05, emissive: col, emissiveIntensity: 0.25 })); g.position.set(-0.3 + i * 0.2, 0.14, (i % 2 - 0.5) * 0.25); loot.add(g); });
const glow = new THREE.PointLight('#ffcc55', 0, 6, 1.6); scene.add(glow);
// جسيمات: تراب، عملات طائرة، بريق، قصاصات
function pool(n, mk) { const a = []; for (let i = 0; i < n; i++) { const m = mk(i); m.visible = false; scene.add(m); a.push(m); } return a; }
const dirt = pool(30, () => rbox(0.26, 0.26, 0.26, '#7a4a28', { r: 0.05 }));
const pile = pool(10, () => rbox(0.5, 0.32, 0.5, '#6e4426', { r: 0.1 }));
const flyCoins = pool(22, () => new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.035, 20), GM));
const spark = pool(40, () => new THREE.Mesh(new THREE.BoxGeometry(0.07, 0.07, 0.07), new THREE.MeshBasicMaterial({ color: '#fff3b0' })));
const CONF = ['#ff3b6b', '#ffd23f', '#33d1ff', '#7cff6b', '#c77dff', '#ff8c42'];
const conf = pool(70, i => rbox(0.14, 0.14, 0.03, CONF[i % 6], { r: 0.02, shadow: false }));

/* ------------------------------ الشخصيات ------------------------------ */
const sanad = character({ skin: '#f2c49b', shirt: '#ff7a1a', stripe: '#ffffff', pants: '#2f4ab0', shoes: '#f4f4f4', hairColor: '#4a2c17',
  hair: [[0.92, 0.22, 0.92, 0, 0.42, 0], [0.92, 0.5, 0.2, 0, 0.2, -0.38], [0.3, 0.16, 0.2, 0.25, 0.32, 0.4]] });
const mirai = character({ skin: '#f7d2b5', shirt: '#ff5fa2', skirt: '#ff86bd', sleeve: '#ff5fa2', pants: '#f7d2b5', shoes: '#7b61ff', hairColor: '#3b2a4f',
  hair: [[0.94, 0.24, 0.94, 0, 0.42, 0], [0.94, 0.8, 0.2, 0, 0.05, -0.4], [0.24, 0.6, 0.24, -0.55, -0.05, -0.05], [0.24, 0.6, 0.24, 0.55, -0.05, -0.05], [0.3, 0.18, 0.16, 0.3, 0.52, 0.38]] });
const bow = rbox(0.34, 0.2, 0.12, '#ffd23f', { r: 0.05 }); bow.position.set(0.32, 0.5, 0); mirai.head.add(bow);
const keeper = character({ skin: '#e8b58e', shirt: '#7b3fe4', stripe: '#ffd23f', pants: '#3a3a4a', shoes: '#222', hairColor: '#9a9a9a', hair: [[0.94, 0.14, 0.94, 0, 0.44, 0]] });
const must = rbox(0.42, 0.1, 0.06, '#3a2a1a', { r: 0.04 }); must.position.set(0, -0.1, 0.44); keeper.head.add(must);
scene.add(sanad.root, mirai.root, keeper.root);

/* ------------------------------ محل الذهب (بعيداً عن الحقل) ------------------------------ */
const SHOP = 40, shop = new THREE.Group(); shop.position.x = SHOP; scene.add(shop);
for (let x = -6; x <= 6; x++) for (let z = -5; z <= 5; z++) { const m = rbox(1, 0.2, 1, (x + z) % 2 ? '#fff4dc' : '#f2d7a8', { r: 0.04, rough: 0.3 }); m.position.set(x, -0.1, z); shop.add(m); }
const wall = rbox(13, 7, 0.4, '#ffe6f0', { r: 0.05, rough: 0.5 }); wall.position.set(0, 3.4, -3.4); shop.add(wall);
for (let i = -6; i <= 6; i++) { const s = rbox(1, 0.8, 0.5, i % 2 ? '#ff4d6d' : '#ffffff', { r: 0.1 }); s.position.set(i, 6.1, -2.9); shop.add(s); }
const sign = rbox(3.2, 1.2, 0.2, '#3a1f5c', { r: 0.1 }); sign.position.set(0, 5.0, -3.1); shop.add(sign);
for (let i = 0; i < 3; i++) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.32, 0.3), gold({ ei: 0.5 })); b.position.set(-0.4 + i * 0.4 + (i === 2 ? -0.6 : 0), 4.85 + (i === 2 ? 0.34 : 0), -2.95); shop.add(b); }
const counter = rbox(4.2, 1.2, 1.2, '#b06b3c', { rough: 0.35 }); counter.position.set(0, 0.6, -0.6); shop.add(counter);
const glass = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.08, 1.2), new THREE.MeshStandardMaterial({ color: '#cfefff', transparent: true, opacity: 0.45, roughness: 0.05, metalness: 0.2 })); glass.position.set(0, 1.24, -0.6); shop.add(glass);
for (let i = 0; i < 7; i++) { const ring = new THREE.Mesh(new THREE.TorusGeometry(0.16, 0.05, 12, 24), gold({ ei: 0.4 })); ring.position.set(-4.4 + (i % 4) * 0.5, 2.2 + Math.floor(i / 4) * 0.7, -3.05); shop.add(ring);
  const ring2 = ring.clone(); ring2.position.x = 3.0 + (i % 4) * 0.5; shop.add(ring2); }
[-4.6, 2.8].forEach(x => { const sh = rbox(2.2, 0.12, 0.6, '#ffffff', { r: 0.04 }); sh.position.set(x + 0.9, 1.9, -3.0); shop.add(sh); const sh2 = sh.clone(); sh2.position.y = 2.6; shop.add(sh2); });
const money = pool(6, () => { const g = new THREE.Group(); const b = rbox(0.7, 0.18, 0.36, '#38c172', { r: 0.03 }); g.add(b); const band = rbox(0.12, 0.2, 0.38, '#ffffff', { r: 0.02 }); g.add(band); return g; });
const bills = pool(40, i => rbox(0.3, 0.02, 0.15, i % 2 ? '#38c172' : '#2fa864', { r: 0.008, shadow: false }));

/* ------------------------------ فقاعة فكرة ميراي (رسم بلا كتابة) ------------------------------ */
function bubbleTex() { const c = document.createElement('canvas'); c.width = 768; c.height = 420; const g = c.getContext('2d');
  g.fillStyle = '#fff'; g.strokeStyle = '#3b2a4f'; g.lineWidth = 10; g.beginPath();
  [[384, 200, 330, 170]].forEach(([x, y, rx, ry]) => g.ellipse(x, y, rx, ry, 0, 0, 7)); g.fill(); g.stroke();
  // صندوق ← محل ذهب ← نقود
  const chestI = (x, y) => { g.fillStyle = '#a0522d'; g.fillRect(x - 60, y - 20, 120, 70); g.fillStyle = '#8b4513'; g.fillRect(x - 62, y - 50, 124, 34); g.fillStyle = '#ffc93c'; g.fillRect(x - 50, y - 50, 16, 100); g.fillRect(x + 34, y - 50, 16, 100); g.fillRect(x - 10, y - 18, 20, 24); };
  const arrow = (x, y) => { g.fillStyle = '#ff5fa2'; g.beginPath(); g.moveTo(x - 30, y - 12); g.lineTo(x + 6, y - 12); g.lineTo(x + 6, y - 28); g.lineTo(x + 34, y); g.lineTo(x + 6, y + 28); g.lineTo(x + 6, y + 12); g.lineTo(x - 30, y + 12); g.fill(); };
  const shopI = (x, y) => { g.fillStyle = '#ffe6f0'; g.fillRect(x - 60, y - 30, 120, 90); for (let i = 0; i < 6; i++) { g.fillStyle = i % 2 ? '#ff4d6d' : '#fff'; g.fillRect(x - 66 + i * 22, y - 52, 22, 26); } g.fillStyle = '#3a1f5c'; g.fillRect(x - 40, y - 24, 80, 34); g.fillStyle = '#ffc93c'; g.fillRect(x - 24, y - 16, 48, 18); g.fillStyle = '#b06b3c'; g.fillRect(x - 18, y + 20, 36, 40); };
  const moneyI = (x, y) => { for (let k = 0; k < 3; k++) { g.fillStyle = '#38c172'; g.fillRect(x - 55, y + 20 - k * 22, 110, 18); g.fillStyle = '#fff'; g.fillRect(x - 8, y + 20 - k * 22, 16, 18); } g.fillStyle = '#ffc93c'; g.beginPath(); g.arc(x + 40, y - 52, 20, 0, 7); g.fill(); };
  chestI(150, 210); arrow(258, 205); shopI(384, 205); arrow(500, 205); moneyI(615, 205);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; }
const bubble = new THREE.Sprite(new THREE.SpriteMaterial({ map: bubbleTex(), transparent: true })); bubble.scale.set(3.0, 1.64, 1); scene.add(bubble);
const dots = pool(3, i => new THREE.Mesh(new THREE.SphereGeometry(0.08 + i * 0.05, 16, 12), new THREE.MeshStandardMaterial({ color: '#fff', roughness: 0.4 })));

/* ------------------------------ الكاميرا بنقاط مفتاحية ------------------------------ */
const CAM = [ // [t, pos, look]
  [0, [6.5, 4.4, 15], [3.0, 1.6, -1]], [4.4, [3.6, 3.6, 10.5], [1.6, 1.4, -1]],
  [4.6, [5.2, 3.2, 4.6], [1.4, 1.1, -0.8]], [9.4, [4.8, 3.0, 4.2], [1.3, 1.0, -0.9]],
  [9.6, [2.6, 2.4, 2.2], [1, 0.1, -1]], [11.9, [2.3, 2.3, 2.0], [1, 0.2, -1]],
  [12.0, [4.4, 2.8, 4.0], [1, 0.9, -0.8]], [15, [2.2, 3.2, 5.2], [1, 1.2, -0.6]], [18.4, [-0.6, 3.6, 6.4], [0.8, 1.3, -0.6]],
  [18.6, [0.8, 3.6, 9.2], [0, 1.7, -0.4]], [21.0, [0.4, 3.8, 9.6], [0.2, 2.6, -0.4]], [23.6, [0.4, 3.8, 9.6], [0.2, 2.6, -0.4]], [25, [0.6, 3.3, 8.6], [0, 1.9, -0.4]],
  [25.1, [SHOP + 7.5, 4.4, 8.0], [SHOP + 0.2, 1.5, -0.6]], [32, [SHOP + 6.4, 3.8, 6.8], [SHOP, 1.6, -0.6]],
  [32.1, [2.0, 2.8, 6.4], [0.6, 1.2, -1]], [37, [3.0, 7.5, 12.5], [0.2, 2.2, -1.6]],
];
function camAt(t) { let i = 0; while (i < CAM.length - 1 && CAM[i + 1][0] <= t) i++; const a = CAM[i], b = CAM[Math.min(i + 1, CAM.length - 1)];
  const q = b === a ? 0 : sm((t - a[0]) / (b[0] - a[0])); const cut = b[0] - a[0] < 0.25;   // فاصل قصير = قطع مباشر
  const p = cut ? a : null; const mix = (u, v) => u.map((x, k) => lerp(x, v[k], p ? 0 : q));
  return { pos: mix(a[1], b[1]), look: mix(a[2], b[2]) }; }

/* ------------------------------ المشهد عبر الزمن ------------------------------ */
const STROKES = [5.3, 6.1, 6.9, 7.7, 8.5], CLANG = 9.7, OPEN = 14.2;
function place(ch, x, z, ry) { ch.root.position.set(x, 0, z); ch.root.rotation.y = ry; }
function holdAt(obj, ch, side, off = [0, -0.9, 0.05]) { ch.root.updateMatrixWorld(true); const arm = side === 'L' ? ch.aL : ch.aR; obj.position.copy(arm.localToWorld(V(...off))); obj.quaternion.copy(arm.getWorldQuaternion(new THREE.Quaternion())); }

function update(t) {
  clouds.forEach((c, i) => { c.position.x = -14 + i * 7 + t * 0.25; });
  // --- سند
  let sx = 2.3, sz = -1, sry = -PI / 2, P0 = {};
  [sanad, mirai, keeper].forEach(c => c.root.visible = true);
  if (t < 4.4) { const q = seg(t, 0, 4.2); sx = lerp(7.5, 2.3, sm(q * 1.1)); P0 = q < 0.98 ? walk(t) : {}; setFace(sanad, 'happy'); }
  else if (t < CLANG) { // يضع الفرع ثم يحفر
    const s = STROKES.find(s0 => t >= s0 - 0.4 && t < s0 + 0.4); const k = s ? Math.sin(clamp((t - (s - 0.4)) / 0.8) * PI) : 0;
    P0 = { aL: -1.4 + k * 0.9, aR: -1.4 + k * 0.9, lean: 0.25 + k * 0.15, lL: -0.2, lR: 0.15 }; if (t < 5.0) P0 = { aL: -0.8 * sm(seg(t, 4.4, 4.8)), aR: -0.4, lean: 0.35 * sm(seg(t, 4.4, 4.8)) };
    setFace(sanad, 'happy');
  } else if (t < 12.0) { const k = clamp((t - CLANG) / 0.25); P0 = { aL: -1.4 + 0.6 * (1 - k), aR: -1.4 + 0.6 * (1 - k), lean: -0.15, y: Math.sin(clamp((t - CLANG) / 0.4) * PI) * 0.25 }; setFace(sanad, 'shock'); }
  else if (t < OPEN) { const k = seg(t, 12.1, 13.6); P0 = { aL: lerp(-0.6, -2.6, sm(k)), aR: lerp(-0.6, -2.6, sm(k)), lean: lerp(0.5, 0, k), lL: -0.3, lR: 0.3 }; setFace(sanad, t < 13 ? 'shock' : 'happy'); }
  else if (t < 18.5) { const j = Math.abs(Math.sin((t - 15) * 5)); P0 = t > 15 ? { aL: -2.8, aR: -2.8, aLz: 0.3, aRz: -0.3, y: j * 0.5, lL: 0.3 * j, lR: -0.3 * j } : { aL: -0.6, aR: -0.6, lean: 0.2 }; setFace(sanad, t > 14.4 ? 'star' : 'shock'); sry = -PI / 2 + sm(seg(t, 15.2, 16)) * PI / 2.2; }
  else if (t < 25) { sry = lerp(-PI / 2 + PI / 2.2, -PI / 3, sm(seg(t, 18.5, 19.5))); P0 = t > 23.6 ? { nod: Math.max(0, Math.sin((t - 23.6) * 8)) * 0.3 } : {}; setFace(sanad, t > 23.4 ? 'laugh' : 'happy'); }
  else if (t < 32) { // في المحل: يحمل الصندوق ثم يضعه
    const q = seg(t, 25, 27); sx = lerp(SHOP + 2.8, SHOP + 0.6, sm(q)); sz = 0.9; sry = PI * 0.82; P0 = q < 1 ? { ...walk(t, 0.7), aL: -1.3, aR: -1.3 } : { aL: lerp(-1.3, 0, seg(t, 27, 27.4)), aR: lerp(-1.3, 0, seg(t, 27, 27.4)) };
    if (t > 29.2) { const j = Math.abs(Math.sin((t - 29.2) * 6)); P0 = { aL: -2.8, aR: -2.8, aLz: 0.3, aRz: -0.3, y: j * 0.45 }; }
    setFace(sanad, t > 28.6 ? 'star' : 'happy');
  } else { // يزرعان الفرع
    sx = 2.2; sz = -0.6; sry = -PI / 2.6; const j = t > 34.6 ? Math.abs(Math.sin((t - 34.6) * 6)) : 0;
    P0 = t < 33.2 ? { aL: -0.9, aR: -0.9, lean: 0.45 } : { aL: -2.8 * (j > 0 ? 1 : 0.2), aR: -2.8 * (j > 0 ? 1 : 0.2), aLz: 0.3, aRz: -0.3, y: j * 0.45 };
    setFace(sanad, t > 34.4 ? 'laugh' : 'happy');
  }
  place(sanad, sx, sz, sry); pose(sanad, P0);
  // --- ميراي
  let mx = -7, mz = 0.6, mry = PI / 2, M = {};
  if (t < 18.5) mirai.root.visible = false;
  else if (t < 25) { const q = seg(t, 18.5, 20.4); mx = lerp(-6.5, -0.4, sm(q)); M = q < 1 ? walk(t) : {}; mry = PI / 2 - (q >= 1 ? 0.35 : 0);
    if (t > 21 && t < 23.4) M = { aR: -2.0, aRz: -0.6, nod: 0.12, tilt: 0.15 };
    if (t >= 23.4) M = { aR: -1.6, aRz: 0.1, turn: 0.2 };
    setFace(mirai, t < 20.4 ? 'happy' : t < 21 ? 'shock' : t < 23.4 ? 'think' : 'wink'); }
  else if (t < 32) { const q = seg(t, 25, 27); mx = lerp(SHOP - 3, SHOP - 0.9, sm(q)); mz = 0.9; mry = PI * 0.82; M = q < 1 ? walk(t) : {};
    if (t > 29.2) { const j = Math.abs(Math.sin((t - 29.35) * 6)); M = { aL: -2.8, aR: -2.8, aLz: 0.3, aRz: -0.3, y: j * 0.45 }; } setFace(mirai, t > 28.6 ? 'laugh' : 'happy'); }
  else { mx = -0.2; mz = -0.2; mry = PI / 2.4; const j = t > 34.75 ? Math.abs(Math.sin((t - 34.75) * 6)) : 0;
    M = t < 33.2 ? { aR: -0.9, aL: -0.9, lean: 0.45 } : { aL: -2.8 * (j > 0 ? 1 : 0.2), aR: -2.8 * (j > 0 ? 1 : 0.2), aLz: 0.3, aRz: -0.3, y: j * 0.45 }; setFace(mirai, t > 34.4 ? 'laugh' : 'happy'); }
  place(mirai, mx, mz, mry); pose(mirai, M);
  // --- صاحب المحل
  place(keeper, SHOP, -1.8, 0); keeper.root.visible = t >= 25 && t < 32;
  pose(keeper, t > 27.4 && t < 28.2 ? { aL: -1.2, aR: -1.2, lean: 0.25 } : t >= 28.6 && t < 30 ? { aR: -1.4, aL: -1.4 } : {}); setFace(keeper, t > 28.0 && t < 29 ? 'star' : 'happy');
  // --- الفرع
  if (t < 4.6) holdAt(sap, sanad, 'L', [0, -0.9, 0.1]); else if (t < 32) { sap.position.set(2.1, 0, -2.0); sap.rotation.set(0, 0, 0.0); sap.scale.setScalar(1); }
  else { const g = sm(seg(t, 33.2, 34.6)); sap.position.set(HOLE.x, 0, HOLE.z); sap.rotation.set(0, 0, 0); sap.scale.setScalar(1 + g * 2.2); }
  sap.visible = !(t >= 25 && t < 32);
  // --- المجرفة
  shovel.visible = t < 12.1; if (shovel.visible) { holdAt(shovel, sanad, 'R', [0, -0.85, 0.05]); if (t >= 4.4) { shovel.rotateX(-0.5); } else shovel.rotateX(0.4); }
  if (t > CLANG && t < 12.1) shovel.rotateZ(Math.sin(clamp((t - CLANG) / 0.6) * PI * 3) * 0.25 * (1 - clamp((t - CLANG) / 0.6)));
  // --- الحفرة
  const done = STROKES.filter(s => t > s).length, depth = t < 33 ? done / 5 : 0.0;
  tiles[HOLE.x + ',' + HOLE.z].visible = done === 0 || t >= 33.6; pit.visible = done > 0 && t < 33.6;
  pitFloor.position.y = -0.1 - depth * 0.9;
  pile.forEach((p, i) => { const on = i < done * 2 && t < 33; p.visible = on; p.position.set(-0.05 + (i % 3) * 0.32, 0.16 + Math.floor(i / 3) * 0.24, -1.2 + (i % 2) * 0.3); });
  dirt.forEach((d, i) => { const s = STROKES[Math.floor(i / 6)], k = (t - s - 0.05) / 0.7; d.visible = s != null && k > 0 && k < 1;
    if (d.visible) { const a = (i % 6) / 6; d.position.set(HOLE.x - 0.2 - k * (0.9 + a * 0.5), 0.2 + Math.sin(k * PI) * (1.2 + a * 0.6) - k * 0.2, HOLE.z + (a - 0.5) * 0.6); d.rotation.set(k * 6, k * 4, 0); } });
  // --- الصندوق والكنز
  chest.visible = t > CLANG - 0.1 && t < 32;
  if (t < 25) { const up = sm(seg(t, 12.3, 13.6)); chest.position.set(HOLE.x, lerp(-0.95, 0.02, up), HOLE.z + up * 1.0); chest.rotation.set(0, up * 0.25, 0); }
  else { const q = seg(t, 25, 27); chest.position.set(lerp(SHOP + 1.6, SHOP, sm(seg(t, 27, 27.4))), q < 1 ? 1.25 : lerp(1.25, 1.28, 1), lerp(0.4, -0.6, sm(seg(t, 27, 27.4)))); if (q < 1) { holdAt(chest, sanad, 'R', [-0.64, -0.95, 0.45]); chest.rotation.set(0, 0, 0); chest.position.y -= 0.35; } chest.rotation.set(0, 0, 0); }
  const open = t < 25 ? sm(seg(t, OPEN, OPEN + 0.6)) : sm(seg(t, 27.5, 28.1)); lid.rotation.x = -open * 1.95; loot.visible = open > 0.05;
  const shine = t < 25 ? (t > CLANG ? (t < 12 ? 0.6 + Math.sin(t * 20) * 0.2 : open * (2.5 + Math.sin(t * 9) * 0.4)) : 0) : open * 2.5;
  glow.position.copy(chest.position).add(V(0, 1.0, 0.2)); glow.intensity = t < 32 ? shine * 0.9 : 0;
  GM.emissiveIntensity = 0.12 + shine * 0.05;
  flyCoins.forEach((c, i) => { const st = OPEN + 0.25 + i * 0.05, k = (t - st) / 1.1; c.visible = t < 25 && k > 0 && k < 1; if (!c.visible) return; const a = i * 2.39, sp = 0.9 + (i % 4) * 0.25;
    c.position.set(chest.position.x + Math.cos(a) * sp * k, chest.position.y + 0.7 + Math.sin(k * PI) * (1.6 + (i % 3) * 0.4) - k * 0.6, chest.position.z + Math.sin(a) * sp * k); c.rotation.set(k * 9, k * 5, 0); });
  spark.forEach((s, i) => { const per = 1.4, ph = ((t * 0.9 + i * 0.137) % per) / per, base = chest.position; s.visible = chest.visible && shine > 0.3;
    if (s.visible) { const a = i * 2.39; s.position.set(base.x + Math.cos(a) * (0.3 + ph * 0.6), base.y + 0.7 + ph * 2.2, base.z + Math.sin(a) * (0.3 + ph * 0.6)); s.scale.setScalar((1 - ph) * 1.1); s.rotation.set(t * 3 + i, t * 2, 0); } });
  // --- فقاعة فكرة ميراي
  const bIn = eob(seg(t, 21.2, 21.7)), bOut = seg(t, 23.6, 23.9); bubble.visible = t > 21.2 && t < 23.9;
  if (bubble.visible) { const hp = mirai.head.getWorldPosition(V(0, 0, 0)); bubble.position.set(hp.x + 0.6, hp.y + 1.75, hp.z); const s = bIn * (1 - bOut); bubble.scale.set(3.0 * s, 1.64 * s, 1);
    dots.forEach((d, i) => { d.visible = true; d.position.set(hp.x + 0.35 + i * 0.3, hp.y + 0.55 + i * 0.32, hp.z); d.scale.setScalar(s); }); } else dots.forEach(d => d.visible = false);
  // --- المال في المحل
  money.forEach((m, i) => { const st = 28.7 + i * 0.12, k = sm(seg(t, st, st + 0.5)); m.visible = t > st && t < 32; const tx = i < 3 ? SHOP + 0.6 : SHOP - 0.9;
    m.position.set(lerp(SHOP - 0.4 + (i % 3) * 0.4, tx + (i % 3 - 1) * 0.2, k), 1.35 + (i % 3) * 0.2 + Math.sin(k * PI) * 0.6, lerp(-0.9, 0.2, k)); });
  bills.forEach((b, i) => { const R4 = rnd(100 + i), st = 29.3 + R4() * 0.8, k = (t - st) / 2.2; b.visible = k > 0 && k < 1 && t < 32; if (!b.visible) return;
    b.position.set(SHOP + (R4() - 0.5) * 6, 6.5 - k * 6.5, -1 + R4() * 3); b.rotation.set(k * 8 + i, k * 5, Math.sin(k * 12 + i) * 0.6); });
  // --- قصاصات الاحتفال الأخيرة
  conf.forEach((c, i) => { const R5 = rnd(300 + i), st = 34.5 + R5() * 0.6, k = (t - st) / 2.0; c.visible = k > 0 && k < 1; if (!c.visible) return;
    const a = R5() * 6.28, sp = 1 + R5() * 2.2; c.position.set(0.6 + Math.cos(a) * sp * k, 2 + Math.sin(k * PI) * 3.5 - k * 2, -0.6 + Math.sin(a) * sp * k); c.rotation.set(k * 10 + i, k * 7, i); });
  // --- الكاميرا
  const C = camAt(t); cam.position.set(...C.pos); cam.lookAt(...C.look);
  comp.render();
}
window.seek = t => { update(t); return true; };
window.engineReady = Promise.resolve(true);
window.DURATION = 37;
