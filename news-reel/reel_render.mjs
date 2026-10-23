// Render the daily reel template (reel.html) for one work dir with Chromium + ffmpeg.
//   node news-reel/reel_render.mjs --dir=work/reel-2026-10-20 --mode=check   stills of every scene + contact sheet (out/sheet.jpg)
//   node news-reel/reel_render.mjs --dir=work/reel-2026-10-20 --mode=stills --t=6,12.5
//   node news-reel/reel_render.mjs --dir=work/reel-2026-10-20 --mode=video   -> <dir>/out/news.mp4 (30 fps, START..DURATION)
import { chromium } from 'playwright';
import { spawn, execFileSync } from 'node:child_process';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';

const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const dir = path.resolve(args.dir), rel = '/' + path.relative(repo, dir) + '/', out = path.join(dir, 'out');
fs.mkdirSync(out, {recursive: true});
const mime = {'.svg': 'image/svg+xml', '.png': 'image/png', '.json': 'application/json', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.woff': 'font/woff', '.woff2': 'font/woff2', '.webp': 'image/webp'};
const server = http.createServer((q, r) => { const f = path.join(repo, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, {'Content-Type': mime[path.extname(f).toLowerCase()] || 'application/octet-stream'}); r.end(d); }); }).listen(0);
const browser = await chromium.launch({executablePath: process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
const page = await browser.newPage({viewport: {width: 1080, height: 1920}});
const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('response', r => r.status() >= 400 && !r.url().endsWith('favicon.ico') && errors.push(`HTTP ${r.status()} ${r.url()}`));
await page.goto(`http://127.0.0.1:${server.address().port}/news-reel/${args.page || 'reel.html'}?dir=${encodeURIComponent(rel)}`);
try { await page.evaluate(() => window.ready); } catch (e) { errors.push(String(e.message || e)); }
const issues = await page.evaluate(() => window.ISSUES || ['page did not finish loading']);
if (errors.length || issues.length) console.log('ISSUES:\n  ' + [...errors, ...issues].join('\n  '));
if (errors.length) { await browser.close(); server.close(); process.exit(5); }
fs.writeFileSync(path.join(out, 'scenes.json'), JSON.stringify(await page.evaluate(() => window.SCENES || []), null, 1));
const shot = async (t, f) => { await page.evaluate(t => window.seek(t), t); await page.screenshot({path: f, type: 'jpeg', quality: 85}); };
if (args.mode === 'check' || args.mode === 'stills') {
  let ts;
  if (args.mode === 'check') { const sc = await page.evaluate(() => window.SCENES); ts = sc.map(s => +Math.min(s.t1 - .2, s.t0 + Math.max(1.6, (s.t1 - s.t0) * .7)).toFixed(2)); }
  else ts = args.t.split(',').map(Number);
  const files = [];
  for (const t of ts) { const f = path.join(out, `still_${t.toFixed(2)}.jpg`); await shot(t, f); files.push(f); }
  if (args.mode === 'check') {   // contact sheets, 5 frames per row
    const rows = []; for (let i = 0; i < files.length; i += 5) rows.push(files.slice(i, i + 5));
    rows.forEach((r, i) => { while (r.length < 5) r.push(r[r.length - 1]);
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...r.flatMap(f => ['-i', f]), '-filter_complex', `${r.map((_, j) => `[${j}]`).join('')}hstack=5,scale=2400:-1`, path.join(out, `sheet${i + 1}.jpg`)]); });
    console.log('scene times:', ts.join(', '), '\nsheets:', rows.map((_, i) => path.join(out, `sheet${i + 1}.jpg`)).join(' '));
  } else console.log(files.join('\n'));
} else {
  const fps = 30, dur = await page.evaluate(() => window.DURATION), t0 = await page.evaluate(() => window.START);
  const f = path.join(out, 'news.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', f], {stdio: ['pipe', 'inherit', 'inherit']});
  const n = Math.round((dur - t0) * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.seek(t), t0 + i / fps);
    const buf = await page.screenshot({type: 'png'});
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
  console.log('wrote', f);
}
await browser.close(); server.close();
