// Render the reel cover (news-reel/cover.html + <dir>/cover.json) to <dir>/cover.jpg, plus a 4:5 grid-crop preview.
//   node news-reel/cover_render.mjs --dir=work/story
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';

const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const dir = path.resolve(args.dir), rel = '/' + path.relative(repo, dir) + '/';
const mime = {'.png': 'image/png', '.json': 'application/json', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.webp': 'image/webp'};
const server = http.createServer((q, r) => { const f = path.join(repo, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, {'Content-Type': mime[path.extname(f)] || 'application/octet-stream'}); r.end(d); }); }).listen(0);
const browser = await chromium.launch({executablePath: process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
const page = await browser.newPage({viewport: {width: 1080, height: 1920}});
const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('response', r => r.status() >= 400 && !r.url().endsWith('favicon.ico') && errors.push(`HTTP ${r.status()} ${r.url()}`));
await page.goto(`http://127.0.0.1:${server.address().port}/news-reel/cover.html?dir=${encodeURIComponent(rel)}`);
await page.evaluate(() => window.ready);
const issues = await page.evaluate(() => window.ISSUES);
const out = path.join(dir, 'cover.jpg');
await page.screenshot({path: out, type: 'jpeg', quality: 92});
await browser.close(); server.close();
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', out, '-vf', 'crop=1080:1350:0:285,scale=540:-1', path.join(dir, 'cover_grid.jpg')]);
if (errors.length || issues.length) { console.log('ISSUES:\n  ' + [...errors, ...issues].join('\n  ')); process.exit(5); }
console.log(out);
