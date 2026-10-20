// Render index.html frame by frame to MP4 (or stills) with Chromium + ffmpeg.
//   node render.mjs --mode=stills --t=5,10,18,25,28
//   node render.mjs --mode=video --fps=30 --out=out/news.mp4   (renders scenes.json start..end)
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const root = path.dirname(new URL(import.meta.url).pathname);
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const w = 1080, h = 1920;
const mime = {'.png': 'image/png', '.txt': 'text/plain; charset=utf-8', '.json': 'application/json', '.jpg': 'image/jpeg', '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.png': 'image/png'};
const server = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, {'Content-Type': mime[path.extname(f)] || 'application/octet-stream'}); r.end(d); }); }).listen(0);
const url = `http://127.0.0.1:${server.address().port}/${args.page || "index.html"}`;
const browser = await chromium.launch({executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const page = await browser.newPage({viewport: {width: w, height: h}});
page.on('pageerror', e => console.log('[pageerror]', e.message));
await page.goto(url); await page.evaluate(() => window.ready);
fs.mkdirSync(path.join(root, 'out'), {recursive: true});
if (args.mode === 'stills') {
  for (const t of (args.t || '1,2,3,5').split(',').map(Number)) {
    await page.evaluate(t => window.seek(t), t);
    await page.screenshot({path: path.join(root, 'out', `still_${w}x${h}_${t.toFixed(2)}.jpg`), type: 'jpeg', quality: 85});
  }
} else {
  const fps = +(args.fps || 30), dur = await page.evaluate(() => window.DURATION), t0 = await page.evaluate(() => window.START);
  const out = path.join(root, args.out || `out/logo-${w}x${h}.mp4`);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], {stdio: ['pipe', 'inherit', 'inherit']});
  const n = Math.round((dur - t0) * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.seek(t), t0 + i / fps);
    const buf = await page.screenshot({type: 'png'});
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
}
await browser.close(); server.close();
