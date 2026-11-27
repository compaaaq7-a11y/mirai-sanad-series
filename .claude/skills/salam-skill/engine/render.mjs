#!/usr/bin/env node
// salam-skill renderer: timeline.json -> mp4 (فريم بفريم عبر Chromium ثم ffmpeg)
//
//   node render.mjs <timeline.json> <out.mp4> [--scale 0.5] [--fps 30] [--from 0 --to 5] [--no-sfx] [--still 3.2,10,21]
//
// --scale 0.5   معاينة سريعة 540x960
// --still t,...  يحفظ صوراً لهذه اللحظات بدل الفيديو (للمراجعة)
import { spawn, execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
// playwright: محلياً أو من التثبيت العام
let chromium;
try { ({ chromium } = await import('playwright')); }
catch { const g = execFileSync('npm', ['root', '-g']).toString().trim(); ({ chromium } = createRequire(path.join(g, 'noop.js'))('playwright')); }
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const flag = k => args.includes('--' + k);
const VALUED = ['--scale', '--fps', '--from', '--to', '--still'];
const [tlPath, outPath] = args.filter((a, i) => !a.startsWith('--') && !VALUED.includes(args[i - 1]));
if (!tlPath || !outPath) { console.error('usage: node render.mjs timeline.json out.mp4 [--scale 0.5] [--fps 30] [--still 1,2]'); process.exit(1); }

const TL = JSON.parse(fs.readFileSync(tlPath, 'utf8'));
const tlDir = path.dirname(path.resolve(tlPath));
const scale = parseFloat(opt('scale', '1'));
const fps = parseInt(opt('fps', TL.fps || 30));
TL.width = Math.round(1080 * scale / 2) * 2; TL.height = Math.round(1920 * scale / 2) * 2;
const t0 = parseFloat(opt('from', '0'));
const t1 = parseFloat(opt('to', TL.duration));

// مجلد عمل: نسخة من المحرك + timeline.js
const work = fs.mkdtempSync(path.join(os.tmpdir(), 'salam-'));
fs.cpSync(here, work, { recursive: true, filter: s => !s.endsWith('.mjs') });
TL.scenes.forEach(s => { if (s.image && !/^(https?|file|data):/.test(s.image)) s.image = 'file://' + path.resolve(tlDir, s.image); });
const abs = x => /^(https?|file|data):/.test(x) ? x : 'file://' + path.resolve(tlDir, x);
TL.scenes.forEach(s => { if (s.stickers) s.stickers = s.stickers.map(abs); if (s.photos) s.photos = s.photos.map(abs); });
TL.scenes.forEach(s => { if (s.prop && s.prop.image && !/^(https?|file|data):/.test(s.prop.image)) s.prop.image = 'file://' + path.resolve(tlDir, s.prop.image); });
// مقاطع الفيديو: Chromium المضمّن لا يشغّل H.264، فنستخرج الفريمات مسبقاً بـ ffmpeg
TL.scenes.forEach((s, i) => {
  if (!s.video) return;
  const src = path.resolve(tlDir, s.video), dir = path.join(work, `vid${i}`);
  fs.mkdirSync(dir, { recursive: true });
  const W = Math.round(1080 * scale / 2) * 2, H = Math.round(1920 * scale / 2) * 2;
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', src, '-vf',
    `fps=${fps},scale=${W}:${H}:force_original_aspect_ratio=increase:flags=lanczos,crop=${W}:${H}`, '-q:v', '2', path.join(dir, '%05d.jpg')]);
  s.frames = { dir: 'file://' + dir, fps, count: fs.readdirSync(dir).length };
  s._videoSrc = src;
});
fs.writeFileSync(path.join(work, 'timeline.js'), 'window.TIMELINE=' + JSON.stringify(TL) + ';');

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: TL.width, height: TL.height }, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto('file://' + path.join(work, 'salam.html'));
await page.evaluate(() => window.engineReady);

const stills = opt('still', null);
if (stills) {
  const base = outPath.replace(/\.(mp4|png|jpg)$/, '');
  for (const s of stills.split(',').map(Number)) {
    await page.evaluate(t => window.seek(t), s);
    const f = `${base}_${s.toFixed(2)}.jpg`;
    await page.screenshot({ path: f, type: 'jpeg', quality: 90 });
    console.log(f);
  }
  await browser.close(); process.exit(0);
}

const silent = path.join(work, 'video.mp4');
const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), silent],
  { stdio: ['pipe', 'inherit', 'inherit'] });
const total = Math.ceil((t1 - t0) * fps);
const started = Date.now();
for (let f = 0; f < total; f++) {
  const t = t0 + f / fps;
  await page.evaluate(tt => window.seek(tt), t);
  const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  if (f % fps === 0) process.stdout.write(`\r  ${(t - t0).toFixed(0)}s / ${(t1 - t0).toFixed(0)}s  (${((Date.now() - started) / 1000).toFixed(0)}s)`);
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log('\n  frames done');

// ---------- الصوت: تعليق + مؤثرات (whoosh عند كل قطع، hit عند الكلمات الحمراء) + موسيقى اختيارية ----------
const voice = TL.audio ? path.resolve(tlDir, TL.audio) : null;
const inputs = [], filters = [], mixes = [];
let n = 1; // الإدخال 0 هو الفيديو الصامت
if (voice && fs.existsSync(voice)) {
  inputs.push('-ss', String(t0), '-t', String(t1 - t0), '-i', voice);
  filters.push(`[${n}:a]aresample=48000,volume=${TL.voice_volume ?? 1}[v]`); mixes.push('[v]'); n++;
}
if (!flag('no-sfx') && TL.sfx !== false) {
  const whoosh = path.join(work, 'whoosh.wav'), hit = path.join(work, 'hit.wav');
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i',
    'anoisesrc=d=0.32:c=pink:a=0.9,highpass=f=500,lowpass=f=7000,afade=t=in:d=0.2:curve=exp,afade=t=out:st=0.2:d=0.12', '-ar', '48000', whoosh]);
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i',
    "aevalsrc='0.9*sin(2*PI*(70-45*t)*t)*exp(-7*t)+0.25*(random(0)-0.5)*exp(-40*t)':d=0.6:s=48000", whoosh.replace('whoosh', 'hit')]);
  const ev = [];
  TL.scenes.forEach((s, i) => { if (i > 0 && !s.soft) ev.push(['w', s.start - 0.12]); });
  TL.scenes.forEach(s => (s.lines || []).flat().forEach(w => { if (w.c === 'red' || w.hit) ev.push(['h', w.t]); }));
  const evs = ev.map(([k, t]) => [k, t - t0]).filter(([, t]) => t >= 0 && t < t1 - t0);
  const W = evs.filter(e => e[0] === 'w'), Hh = evs.filter(e => e[0] === 'h');
  const add = (file, list, vol, tag) => {
    if (!list.length) return;
    inputs.push('-i', file);
    const outs = list.map((_, k) => `[${tag}${k}]`).join('');
    filters.push(`[${n}:a]asplit=${list.length}${outs}`);
    list.forEach(([, t], k) => { filters.push(`[${tag}${k}]adelay=${Math.round(t * 1000)}:all=1,volume=${vol}[${tag}d${k}]`); mixes.push(`[${tag}d${k}]`); });
    n++;
  };
  add(whoosh, W, TL.whoosh_volume ?? 0.35, 'w');
  add(hit, Hh, TL.hit_volume ?? 0.45, 'h');
}
// صوت مقاطع الفيديو (إن وجد) في موضع مشهدها
TL.scenes.forEach(s => {
  if (!s._videoSrc || s.video_volume === 0) return;
  const has = execFileSync('ffprobe', ['-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', s._videoSrc]).toString().trim();
  if (!has) return;
  const st = s.start - t0, len = s.end - s.start;
  if (st + len <= 0 || st >= t1 - t0) return;
  inputs.push('-i', s._videoSrc);
  filters.push(`[${n}:a]aresample=48000,atrim=${s.video_from || 0}:${(s.video_from || 0) + len},asetpts=N/SR/TB,afade=t=out:st=${Math.max(0, len - 0.3).toFixed(2)}:d=0.3,adelay=${Math.round(Math.max(0, st) * 1000)}:all=1,volume=${s.video_volume ?? 1}[va${n}]`);
  mixes.push(`[va${n}]`); n++;
});
if (TL.music) {
  let music = TL.music;
  if (music === 'playful') {
    // موسيقى مرحة للكرتون: نقرات أرپيجيو بنغمات خماسية (150 نبضة) + باص، بلا حقوق
    music = path.join(work, 'bed.wav');
    const N = [523.25, 659.25, 783.99, 659.25, 587.33, 698.46, 880, 698.46, 523.25, 659.25, 783.99, 1046.5, 987.77, 783.99, 659.25, 587.33];
    const step = 0.2, sel = `mod(floor(t/${step}),${N.length})`;
    const freq = N.map((f, k) => `eq(${sel},${k})*${f}`).join('+');
    const pluck = `0.22*sin(2*PI*(${freq})*t)*exp(-9*mod(t,${step}))`;
    const B = [130.81, 174.61, 196, 130.81], bsel = `mod(floor(t/0.8),4)`;
    const bass = `0.25*sin(2*PI*(${B.map((f, k) => `eq(${bsel},${k})*${f}`).join('+')})*t)*exp(-3.5*mod(t,0.8))`;
    const tick = `0.04*(random(0)-0.5)*exp(-70*mod(t+0.1,0.4))`;
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i',
      `aevalsrc='${pluck}+${bass}+${tick}':d=${(t1 - t0 + 1).toFixed(2)}:s=48000`,
      '-af', `lowpass=f=6000,aecho=0.6:0.4:180:0.25,afade=t=in:d=0.3,afade=t=out:st=${Math.max(0, t1 - t0 - 1.2).toFixed(2)}:d=1.2`, music]);
  } else if (music === 'calm') {
    // موسيقى هادئة مولّدة بلا إيقاع للمواضيع العاطفية: تآلفان يتبادلان بنعومة
    music = path.join(work, 'bed.wav');
    const env = `(0.8+0.2*sin(2*PI*0.125*t))`;
    const ch = (a, b, c) => `(0.07*sin(2*PI*${a}*t)+0.05*sin(2*PI*${b}*t)+0.035*sin(2*PI*${c}*t))`;
    const w = `(0.5+0.5*cos(2*PI*t/16))`; // انتقال ناعم بين تآلفين كل 8 ثوانٍ
    const pad = `(${ch(110, 130.81, 164.81)}*${w}+${ch(87.31, 130.81, 174.61)}*(1-${w}))`;
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i',
      `aevalsrc='${pad}*${env}':d=${(t1 - t0 + 1).toFixed(2)}:s=48000`,
      '-af', `lowpass=f=2500,aecho=0.8:0.7:120|240:0.3|0.2,afade=t=in:d=1.5,afade=t=out:st=${Math.max(0, t1 - t0 - 2).toFixed(2)}:d=2`, music]);
  } else if (music === 'auto') {
    // موسيقى خلفية مولّدة: نبض بيس 100bpm + وسادة هادئة (بدون إنترنت أو حقوق)
    music = path.join(work, 'bed.wav');
    const b = 0.6; // طول النبضة بالثواني
    const kick = `0.9*sin(2*PI*(42+70*exp(-28*mod(t,${b})))*mod(t,${b}))*exp(-7*mod(t,${b}))`;
    const pad = `(0.10*sin(2*PI*55*t)+0.07*sin(2*PI*82.41*t)+0.05*sin(2*PI*130.81*t)+0.03*sin(2*PI*164.81*t))*(0.75+0.25*sin(2*PI*0.2*t))`;
    const tick = `0.05*(random(0)-0.5)*exp(-60*mod(t+${b / 2},${b}))`;
    execFileSync('ffmpeg', ['-v', 'error', '-y', '-f', 'lavfi', '-i',
      `aevalsrc='${kick}+${pad}+${tick}':d=${(t1 - t0 + 1).toFixed(2)}:s=48000`,
      '-af', `lowpass=f=5000,afade=t=in:d=0.4,afade=t=out:st=${Math.max(0, t1 - t0 - 1.5).toFixed(2)}:d=1.5`, music]);
  } else music = path.resolve(tlDir, music);
  inputs.push('-stream_loop', '-1', '-i', music);
  filters.push(`[${n}:a]aresample=48000,volume=${TL.music_volume ?? 0.12}[m]`); mixes.push('[m]'); n++;
}
const dur = (t1 - t0).toFixed(3);
if (mixes.length) {
  filters.push(`${mixes.join('')}amix=inputs=${mixes.length}:normalize=0:duration=longest,atrim=0:${dur},alimiter=limit=0.95,loudnorm=I=-14:TP=-1:LRA=7[aout]`);
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', silent, ...inputs, '-filter_complex', filters.join(';'),
    '-map', '0:v', '-map', '[aout]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-t', dur, '-movflags', '+faststart', outPath], { stdio: 'inherit' });
} else {
  fs.copyFileSync(silent, outPath);
}
fs.rmSync(work, { recursive: true, force: true });
console.log('  wrote', outPath);
