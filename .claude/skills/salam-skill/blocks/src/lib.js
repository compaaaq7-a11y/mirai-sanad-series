// مكتبة «عالم المكعبات»: مشهد ثلاثي الأبعاد حتمي (كل شيء دالة في الزمن t) يُرسم إطاراً إطاراً بـ render3d.mjs
import * as THREE from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
export { THREE };

export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const sm = p => { p = clamp(p); return p * p * (3 - 2 * p); };
export const lerp = (a, b, p) => a + (b - a) * p;
export const eob = p => { p = clamp(p); const c = 1.7; return 1 + (c + 1) * Math.pow(p - 1, 3) + c * Math.pow(p - 1, 2); };
export const seg = (t, a, b) => clamp((t - a) / (b - a));
// مولّد عشوائي ثابت (نفس النتيجة في كل إطار)
export function rnd(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

export function setup(W, H, sky = ['#6ec6ff', '#c9ecff']) {
  const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  r.setSize(W, H); r.setPixelRatio(1);
  r.toneMapping = THREE.NeutralToneMapping; r.toneMappingExposure = 0.82;
  r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
  document.body.appendChild(r.domElement);
  const scene = new THREE.Scene();
  // سماء متدرجة
  const c = document.createElement('canvas'); c.width = 4; c.height = 256; const g = c.getContext('2d');
  const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, sky[0]); gr.addColorStop(1, sky[1]); g.fillStyle = gr; g.fillRect(0, 0, 4, 256);
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; scene.background = tx;
  const pm = new THREE.PMREMGenerator(r); scene.environment = pm.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.3;
  const cam = new THREE.PerspectiveCamera(42, W / H, 0.1, 200);
  const hemi = new THREE.HemisphereLight('#dff3ff', '#7a5a3a', 0.7); scene.add(hemi);
  const sun = new THREE.DirectionalLight('#fff4dc', 1.6); sun.position.set(8, 14, 6); sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048); Object.assign(sun.shadow.camera, { left: -14, right: 14, top: 14, bottom: -14, near: 1, far: 50 }); sun.shadow.bias = -0.0004;
  scene.add(sun);
  const comp = new EffectComposer(r); comp.addPass(new RenderPass(scene, cam));
  const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.12, 0.3, 0.985); comp.addPass(bloom); comp.addPass(new OutputPass());
  return { r, scene, cam, sun, comp, bloom };
}

// مكعب لامع بحواف مستديرة (شكل ألعاب حقيقية)
const GEO = new Map();
export function rbox(w, h, d, color, o = {}) {
  const k = `${w},${h},${d},${o.r ?? 0.08}`;
  if (!GEO.has(k)) GEO.set(k, new RoundedBoxGeometry(w, h, d, 3, Math.min(o.r ?? 0.08, Math.min(w, h, d) / 2 - 0.001)));
  const m = new THREE.Mesh(GEO.get(k), new THREE.MeshStandardMaterial({ color, roughness: o.rough ?? 0.28, metalness: o.metal ?? 0.05,
    emissive: o.emissive || '#000', emissiveIntensity: o.ei ?? 1 }));
  m.castShadow = o.shadow !== false; m.receiveShadow = true;
  return m;
}
export function gold(o = {}) { return new THREE.MeshStandardMaterial({ color: '#ffd93b', metalness: 0.55, roughness: 0.22, emissive: '#ffcf1a', emissiveIntensity: o.ei ?? 0.12 }); }

// وجوه مرسومة على مقدمة الرأس
const FACE = {};
export function faceTex(kind, skin) {
  const key = kind + skin; if (FACE[key]) return FACE[key];
  const c = document.createElement('canvas'); c.width = c.height = 256; const g = c.getContext('2d');
  g.fillStyle = skin; g.fillRect(0, 0, 256, 256);
  const eye = (x, y, r = 22) => { g.fillStyle = '#fff'; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); g.fillStyle = '#1b1b2b'; g.beginPath(); g.arc(x + 3, y + 3, r * 0.55, 0, 7); g.fill(); g.fillStyle = '#fff'; g.beginPath(); g.arc(x + 8, y - 4, r * 0.18, 0, 7); g.fill(); };
  const star = (x, y) => { g.fillStyle = '#ffcf1f'; g.strokeStyle = '#b37400'; g.lineWidth = 4; g.beginPath(); for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? 12 : 28; g.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); } g.closePath(); g.fill(); g.stroke(); };
  g.lineCap = 'round'; g.lineWidth = 10; g.strokeStyle = '#1b1b2b';
  const mouth = d => { g.beginPath(); d(); g.stroke(); };
  if (kind === 'star') { star(85, 110); star(171, 110); g.fillStyle = '#8a1c2c'; g.beginPath(); g.ellipse(128, 180, 40, 28, 0, 0, Math.PI); g.fill(); }
  else if (kind === 'shock') { eye(85, 108, 28); eye(171, 108, 28); g.fillStyle = '#8a1c2c'; g.beginPath(); g.ellipse(128, 190, 20, 26, 0, 0, 7); g.fill(); }
  else if (kind === 'laugh') { mouth(() => { g.moveTo(60, 115); g.quadraticCurveTo(85, 90, 110, 115); g.moveTo(146, 115); g.quadraticCurveTo(171, 90, 196, 115); }); g.fillStyle = '#8a1c2c'; g.beginPath(); g.moveTo(80, 160); g.quadraticCurveTo(128, 240, 176, 160); g.closePath(); g.fill(); }
  else if (kind === 'think') { eye(85, 115, 20); eye(171, 112, 20); mouth(() => { g.moveTo(150, 70); g.lineTo(196, 60); g.moveTo(100, 185); g.lineTo(150, 178); }); }
  else if (kind === 'wink') { eye(85, 112); mouth(() => { g.moveTo(146, 115); g.quadraticCurveTo(171, 95, 196, 115); g.moveTo(85, 170); g.quadraticCurveTo(128, 210, 171, 170); }); }
  else { eye(85, 112); eye(171, 112); mouth(() => { g.moveTo(85, 170); g.quadraticCurveTo(128, 210, 171, 170); }); }   // happy
  if (kind !== 'shock') { g.fillStyle = 'rgba(255,120,140,.35)'; g.beginPath(); g.arc(55, 165, 18, 0, 7); g.arc(201, 165, 18, 0, 7); g.fill(); }
  const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; FACE[key] = tx; return tx;
}

// شخصية مكعبات: رأس، جذع، ذراعان، ساقان (مفاصل عند الكتف والورك)
export function character(o) {
  const root = new THREE.Group(), body = new THREE.Group(); root.add(body);
  const legGeo = (col) => { const p = new THREE.Group(); const m = rbox(0.42, 0.9, 0.46, col); m.position.y = -0.45; p.add(m); const sh = rbox(0.46, 0.18, 0.58, o.shoes || '#ffffff'); sh.position.set(0, -0.86, 0.06); p.add(sh); return p; };
  const lL = legGeo(o.pants), lR = legGeo(o.pants); lL.position.set(-0.23, 0.92, 0); lR.position.set(0.23, 0.92, 0); body.add(lL, lR);
  const torso = rbox(0.96, 1.0, 0.52, o.shirt); torso.position.y = 1.42; body.add(torso);
  if (o.stripe) { const s = rbox(0.98, 0.18, 0.54, o.stripe, { r: 0.04 }); s.position.y = 1.45; body.add(s); }
  if (o.skirt) { const sk = rbox(1.08, 0.36, 0.64, o.skirt); sk.position.y = 0.98; body.add(sk); }
  const arm = (col) => { const p = new THREE.Group(); const m = rbox(0.3, 0.84, 0.34, col); m.position.y = -0.38; p.add(m); const h = rbox(0.3, 0.22, 0.34, o.skin); h.position.y = -0.86; p.add(h); return p; };
  const aL = arm(o.sleeve || o.shirt), aR = arm(o.sleeve || o.shirt); aL.position.set(-0.64, 1.86, 0); aR.position.set(0.64, 1.86, 0); body.add(aL, aR);
  const neck = new THREE.Group(); neck.position.y = 1.94; body.add(neck);
  const skinM = new THREE.MeshStandardMaterial({ color: o.skin, roughness: 0.35 });
  const faceM = new THREE.MeshStandardMaterial({ map: faceTex('happy', o.skin), roughness: 0.35 });
  const head = new THREE.Mesh(new RoundedBoxGeometry(0.86, 0.86, 0.86, 3, 0.1), [skinM, skinM, skinM, skinM, faceM, skinM]);
  head.castShadow = true; head.position.y = 0.45; neck.add(head);
  const hair = new THREE.Group(); head.add(hair);
  (o.hair || []).forEach(([w, h, d, x, y, z]) => { const m = rbox(w, h, d, o.hairColor); m.position.set(x, y, z); hair.add(m); });
  return { root, body, lL, lR, aL, aR, neck, head, faceM, skin: o.skin, face: 'happy', hand: aR };
}
export function setFace(ch, kind) { if (ch.face === kind) return; ch.face = kind; ch.faceM.map = faceTex(kind, ch.skin); ch.faceM.needsUpdate = true; }
// وضعية: زوايا بالراديان (x للأمام/الخلف)
export function pose(ch, p) {
  ch.lL.rotation.set(p.lL || 0, 0, 0); ch.lR.rotation.set(p.lR || 0, 0, 0);
  ch.aL.rotation.set(p.aL || 0, 0, p.aLz || 0); ch.aR.rotation.set(p.aR || 0, 0, p.aRz || 0);
  ch.body.position.y = p.y || 0; ch.body.rotation.x = p.lean || 0;
  ch.neck.rotation.set(p.nod || 0, p.turn || 0, p.tilt || 0);
}
export const walk = (t, k = 1) => { const w = Math.sin(t * 9) * 0.6 * k; return { lL: w, lR: -w, aL: -w * 0.9, aR: w * 0.9, y: Math.abs(Math.cos(t * 9)) * 0.06 * k }; };
