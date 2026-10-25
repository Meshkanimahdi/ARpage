// Render every item of <dir>/slides.json with news-reel/slide.html (Persian text typeset in code over a storyboard
// panel) to <dir>/<prefix>-<n>.jpg, plus <dir>/<prefix>_report.json and a contact sheet <dir>/<prefix>_sheet.jpg.
//   node news-reel/slide_render.mjs --dir=work/final/slides [--prefix=slide]
// Exit 5 when any item does not fit or has too many words.
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';

const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const dir = path.resolve(args.dir), rel = '/' + path.relative(repo, dir) + '/', prefix = args.prefix || 'slide';
const S = JSON.parse(fs.readFileSync(path.join(dir, 'slides.json'), 'utf8'));
const story = S.format === 'story', H = story ? 1920 : 1350;
const mime = {'.png': 'image/png', '.json': 'application/json', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.svg': 'image/svg+xml', '.webp': 'image/webp'};
const server = http.createServer((q, r) => { const f = path.join(repo, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, {'Content-Type': mime[path.extname(f)] || 'application/octet-stream'}); r.end(d); }); }).listen(0);
const browser = await chromium.launch({executablePath: process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
const page = await browser.newPage({viewport: {width: 1080, height: H}});
const all = [], files = [];
for (let i = 0; i < S.items.length; i++) {
  const errors = []; const onErr = e => errors.push(e.message); page.on('pageerror', onErr);
  await page.goto(`http://127.0.0.1:${server.address().port}/news-reel/slide.html?dir=${encodeURIComponent(rel)}&i=${i}`);
  await page.evaluate(() => window.ready);
  const rep = await page.evaluate(() => Object.assign({}, window.REPORT, {issues: window.ISSUES}));
  rep.issues.push(...errors); page.off('pageerror', onErr);
  const f = path.join(dir, `${prefix}-${i + 1}.jpg`);
  await page.screenshot({path: f, type: 'jpeg', quality: 92}); files.push(f); all.push(rep);
}
await browser.close(); server.close();
fs.writeFileSync(path.join(dir, `${prefix}_report.json`), JSON.stringify(all, null, 1));
const cols = Math.min(files.length, story ? 3 : 3);
execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...files.flatMap(f => ['-i', f]), '-filter_complex',
  files.map((_, j) => `[${j}]scale=360:-1[s${j}]`).join(';') + ';' + files.map((_, j) => `[s${j}]`).join('') +
  `xstack=inputs=${files.length}:layout=` + files.map((_, j) => `${(j % cols) * 360}_${Math.floor(j / cols) * (H / 3)}`).join('|'),
  path.join(dir, `${prefix}_sheet.jpg`)]);
const bad = all.filter(r => r.issues.length);
if (bad.length) { console.log('ISSUES:\n  ' + bad.flatMap(r => r.issues).join('\n  ')); process.exit(5); }
console.log(files.join('\n'));
