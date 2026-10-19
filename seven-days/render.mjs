import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const root = path.dirname(new URL(import.meta.url).pathname);
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const mime = {'.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.mp3': 'audio/mpeg', '.ogg': 'audio/ogg', '.wav': 'audio/wav', '.json': 'application/json'};
const server = http.createServer((q, r) => { const f = path.join(root, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, {'Content-Type': mime[path.extname(f)] || 'application/octet-stream'}); r.end(d); }); }).listen(0);
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--autoplay-policy=no-user-gesture-required']});
const page = await browser.newPage({viewport: {width: 1920, height: 1080}});
page.on('console', m => console.log('[page]', m.text()));
page.on('pageerror', e => console.log('[pageerror]', e.message));

if (args.mode === 'stills') {
  await page.goto(base + '/index.html'); await page.evaluate(() => window.ready);
  const ts = (args.t || '1,7,14,20').split(',').map(Number);
  const sd = path.join(root, 'out', args.dir || 'stills'); fs.mkdirSync(sd, {recursive: true});
  for (const t of ts) { await page.evaluate(t => window.seek(t), t); await page.screenshot({path: path.join(sd, `t${String(t.toFixed(2)).padStart(6, '0')}.jpg`), type: 'jpeg', quality: 80}); }
} else if (args.mode === 'video') {
  await page.goto(base + '/index.html'); await page.evaluate(() => window.ready);
  const fps = +(args.fps || 30), dur = await page.evaluate(() => window.DURATION);
  const from = +(args.from || 0), to = Math.min(dur, +(args.to || dur));
  const out = path.join(root, args.out || 'out/picture.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(fps), out], {stdio: ['pipe', 'inherit', 'inherit']});
  const n = Math.round((to - from) * fps); const t0 = Date.now();
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.seek(t), from + i / fps);
    const buf = await page.screenshot({type: 'jpeg', quality: 92});
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('wrote', out);
} else if (args.mode === 'audio') {
  await page.goto(base + '/audio.html');
  const b64 = await page.evaluate(async () => await window.renderMix(), {timeout: 0});
  fs.writeFileSync(path.join(root, args.out || 'out/mix.wav'), Buffer.from(b64, 'base64'));
  console.log('wrote audio');
}
await browser.close(); server.close();
