// Bake one 360° panorama per station from the image-projected model.
//   cd airbnb-3d-tour && python3 -m http.server 8000 &
//   node tools/bake-panos.js http://localhost:8000 panos [width]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [,, base, out, width = '3072'] = process.argv;
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1000, height: 700 } });
  p.on('pageerror', (e) => console.error(e.message));
  if (process.env.THREE_DIR) await p.route('https://cdn.jsdelivr.net/npm/three@0.147.0/**', (r) => r.fulfill({ path: path.join(process.env.THREE_DIR, r.request().url().split('three@0.147.0/')[1]), contentType: 'application/javascript' }));
  await p.goto(base + '/tour.html#embed');
  await p.waitForFunction(() => window.TOUR && window.HOME);
  const ids = await p.evaluate(() => window.HOME.PHOTOS.map((q) => q.n));
  await p.evaluate(() => window.TOUR.show());
  await p.waitForTimeout(1500);
  await p.evaluate(() => window.TOUR.bakePano(1, 64));          // warm up: loads the 18 images into the atlas
  await p.waitForTimeout(4000);
  fs.mkdirSync(out, { recursive: true });
  for (const n of ids) {
    const url = await p.evaluate(([n, w]) => window.TOUR.bakePano(n, w), [n, +width]);
    fs.writeFileSync(path.join(out, `pano${String(n).padStart(2, '0')}.jpg`), Buffer.from(url.split(',')[1], 'base64'));
    console.log('pano', n);
  }
  await b.close();
})();
