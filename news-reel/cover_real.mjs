// Realistic photo covers (news-reel/cover_real.html). Input: a JSON list [{id, bg, title, style?, pos?, a?, fs?, out}].
// style = bold | poster | serif | kufi | tech | soft (headline font and accent treatment; rotate, RUNBOOK header rules).
//   node news-reel/cover_real.mjs covers.json
// Writes each <out> plus <out>.report.json {font_px, pos, top, bottom, lines, words, md5, issues}. Exit 5 when a headline does
// not fit the safe band (y 500–1420, 90 px side margins; Mahdi 2026-11-18): shorten it, never move it to an edge.
import { chromium } from 'playwright'; import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path'; import crypto from 'node:crypto';
const repo = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const mime = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.html': 'text/html', '.woff2': 'font/woff2'};
const srv = http.createServer((q, r) => { const f = path.join(repo, decodeURIComponent(q.url.split('?')[0])); fs.readFile(f, (e, d) => { if (e) { r.writeHead(404); r.end(); return; } r.writeHead(200, {'Content-Type': mime[path.extname(f)] || 'application/octet-stream'}); r.end(d); }); }).listen(0);
const V = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const b = await chromium.launch({executablePath: process.env.CHROME || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'}); const p = await b.newPage({viewport: {width: 1080, height: 1920}});
let failed = 0;
for (const v of V) {
  const u = `http://127.0.0.1:${srv.address().port}/news-reel/cover_real.html?` + new URLSearchParams({bg: v.bg, title: v.title, pos: v.pos || 'center', style: v.style || 'bold', a: v.a || '', ...(v.fs ? {fs: String(v.fs)} : {})});
  await p.goto(u); await p.evaluate(() => window.ok); await p.waitForTimeout(200);
  await p.screenshot({path: v.out, type: 'jpeg', quality: 92});
  const rep = await p.evaluate(() => Object.assign({}, window.REPORT, {issues: window.ISSUES}));
  rep.md5 = crypto.createHash('md5').update(fs.readFileSync(v.out)).digest('hex');
  fs.writeFileSync(v.out + '.report.json', JSON.stringify(rep, null, 1));
  if (path.basename(v.out) === 'cover.jpg') fs.writeFileSync(path.join(path.dirname(v.out), 'cover_report.json'), JSON.stringify(rep, null, 1));   // what reel_gate.py reads
  if (rep.issues.length) { failed++; console.log(v.id, 'ISSUES:', rep.issues.join('; ')); } else console.log(v.id, `ok ${rep.style} ${rep.render_px}px ${rep.pos} y ${rep.top}–${rep.bottom}`);
}
await b.close(); srv.close(); process.exit(failed ? 5 : 0);
