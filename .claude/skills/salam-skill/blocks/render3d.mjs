// إخراج مشهد «عالم المكعبات» إلى فيديو: node render3d.mjs <scene> out.mp4 [--w 540 --h 960 --fps 30 --still 1,5 --audio a.wav]
import { createRequire } from 'module'; import fs from 'fs'; import path from 'path'; import { spawn, execFileSync } from 'child_process';
const require = createRequire(import.meta.url); const { chromium } = require('playwright');
const here = path.dirname(new URL(import.meta.url).pathname);
const a = process.argv.slice(2), opt = (k, d) => { const i = a.indexOf('--' + k); return i >= 0 ? a[i + 1] : d; };
const scene = a[0], out = a[1], W = +opt('w', 540), H = +opt('h', 960), fps = +opt('fps', 30);
fs.mkdirSync(path.join(here, 'dist'), { recursive: true });
execFileSync(path.join(here, 'node_modules/.bin/esbuild'), [path.join(here, 'src', scene + '.js'), '--bundle', '--format=iife', '--log-level=warning', '--outfile=' + path.join(here, 'dist', scene + '.js')]);
fs.writeFileSync(path.join(here, 'dist', scene + '.html'), `<!doctype html><html><body style="margin:0;background:#000;overflow:hidden"><script src="${scene}.js"></script></body></html>`);
const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: W, height: H } });
p.on('pageerror', e => console.error('page error:', e.message));
await p.goto(`file://${path.join(here, 'dist', scene + '.html')}?w=${W}&h=${H}`); await p.evaluate(() => window.engineReady);
const D = await p.evaluate(() => window.DURATION);
const stills = opt('still', null);
if (stills) { for (const s of stills.split(',').map(Number)) { await p.evaluate(t => window.seek(t), s); const f = out.replace(/\.(mp4|png|jpg)$/, '') + `_${s.toFixed(2)}.jpg`; await p.screenshot({ path: f, type: 'jpeg', quality: 90 }); console.log(f); } await b.close(); process.exit(0); }
const silent = out.replace(/\.mp4$/, '.silent.mp4');
const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', silent], { stdio: ['pipe', 'inherit', 'inherit'] });
const N = Math.ceil(D * fps), t0 = Date.now();
for (let f = 0; f < N; f++) { await p.evaluate(t => window.seek(t), f / fps); const buf = await p.screenshot({ type: 'jpeg', quality: 93 }); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); if (f % fps === 0) process.stdout.write(`\r  ${(f / fps).toFixed(0)}s/${D}s (${((Date.now() - t0) / 1000).toFixed(0)}s)`); }
ff.stdin.end(); await new Promise(r => ff.on('close', r)); await b.close();
const audio = opt('audio', null);
if (audio) { execFileSync('ffmpeg', ['-v', 'error', '-y', '-i', silent, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-af', 'loudnorm=I=-14:TP=-1:LRA=7', '-shortest', '-movflags', '+faststart', out]); fs.unlinkSync(silent); }
else fs.renameSync(silent, out);
console.log('\n  wrote', out);
