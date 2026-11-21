// Open the finished tour in a real browser and visit every point, the way a visitor would.
//   node test_tour.js TOUR.html_or_URL SHOTS_DIR [--three /path/to/three.min.js] [--look N,PLANX,PLANY ...]
// Checks: the page starts, every panorama loads, no script errors, a doorway label takes you through, the plan sheet opens.
// Writes one screenshot per point (desktop) plus a phone-sized one of the first point; --look adds views toward a plan point.
// --three serves Three.js from disk when the CDN cannot be reached from where the test runs.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const args = process.argv.slice(2);
  const target = args[0], out = args[1];
  const three = args.includes('--three') ? fs.readFileSync(args[args.indexOf('--three') + 1], 'utf8') : null;
  const looks = args.filter((a, i) => args[i - 1] === '--look').map(s => s.split(',').map(Number));
  const url = /^https?:/.test(target) ? target : 'file://' + path.resolve(target);
  fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch({ args: ['--use-gl=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  let failed = false;
  for (const [name, vp] of [['desk', { width: 1440, height: 810 }], ['phone', { width: 390, height: 780 }]]) {
    const p = await b.newPage({ viewport: vp, deviceScaleFactor: 1 });
    const errs = []; p.on('pageerror', e => errs.push(String(e)));
    if (three) await p.route('**/three.min.js', r => r.fulfill({ body: three, contentType: 'application/javascript' }));
    await p.goto(url);
    await p.waitForFunction(() => window.TOUR360 && document.getElementById('pt').textContent !== '—', null, { timeout: 90000 });
    const nodes = await p.evaluate(() => window.HOME.NODES.map(q => ({ n: q.n, x: q.x, y: q.y })));
    const still = async (yaw) => { await p.mouse.move(vp.width / 2, vp.height / 2); await p.mouse.down(); await p.mouse.up(); if (yaw !== undefined) await p.evaluate((y) => window.TOUR360.look(y, 0), yaw); await p.waitForTimeout(500); };
    for (const q of (name === 'desk' ? nodes : nodes.slice(0, 1))) {
      await p.evaluate((n) => window.TOUR360.go(n, { instant: true }), q.n);
      await p.waitForTimeout(1300);
      const state = await p.evaluate(() => ({ hash: location.hash, hidden: document.getElementById('load').style.opacity }));
      if (state.hash !== '#p' + q.n || state.hidden !== '0') { errs.push('point ' + q.n + ' did not load'); }
      await still();
      await p.screenshot({ path: `${out}/${name}_${String(q.n).padStart(2, '0')}.jpg`, quality: 82, type: 'jpeg' });
    }
    if (name === 'desk') {
      for (const [n, x, y] of looks) {
        const q = nodes.find(k => k.n === n);
        await p.evaluate((n) => window.TOUR360.go(n, { instant: true }), n); await p.waitForTimeout(1300);
        await still(Math.atan2(-(x - q.x), -(y - q.y)));
        await p.screenshot({ path: `${out}/look_${n}_${x}_${y}.jpg`, quality: 85, type: 'jpeg' });
      }
      const withDoor = nodes.find(q => true);
      await p.evaluate((n) => window.TOUR360.go(n, { instant: true }), withDoor.n); await p.waitForTimeout(900);
      const tag = await p.evaluate(() => { const t = document.querySelector('.tag'); if (t) { t.click(); return t.textContent; } return null; });
      if (tag) { await p.waitForTimeout(2600); const now = await p.evaluate(() => location.hash); if (now === '#p' + withDoor.n) errs.push('doorway label "' + tag + '" did not move the visitor'); }
      await p.evaluate(() => document.getElementById('bPlan').click()); await p.waitForTimeout(500);
      await p.screenshot({ path: `${out}/plan.jpg`, quality: 85, type: 'jpeg' });
      const dots = await p.evaluate(() => document.querySelectorAll('#planSvg .node').length);
      if (dots !== nodes.length) errs.push('plan sheet shows ' + dots + ' points, expected ' + nodes.length);
    }
    console.log(name + ':', errs.length ? 'FAILED - ' + errs.join(' ; ') : 'ok, ' + (name === 'desk' ? nodes.length : 1) + ' point(s) visited');
    failed = failed || errs.length > 0;
    await p.close();
  }
  await b.close();
  process.exit(failed ? 1 : 0);
})();
