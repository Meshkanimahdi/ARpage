// Turn the plan SVG into a PNG to send:  node svg2png.js plan.svg plan.png [width]
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [src, dst, w] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: +(w || 2000), height: 1400 } });
  await p.goto('file://' + path.resolve(src));
  await p.waitForTimeout(600);
  const box = await p.evaluate(() => { const v = document.documentElement.viewBox.baseVal; return v.height / v.width; });
  await p.setViewportSize({ width: +(w || 2000), height: Math.round(+(w || 2000) * box) });
  await p.screenshot({ path: dst });
  await b.close();
})();
