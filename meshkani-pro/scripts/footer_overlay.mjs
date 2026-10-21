// usage: node footer_overlay.mjs <in.jpg|png> <out.jpg> <n|story> <light|dark|pill> [ink-hex]   (run from the repo root after news-reel/setup.sh)
// Post (n = 1..3): adds handle, «n از ۳» and «تصویر مفهومی» at exact coordinates inside the 8% safe margins.
// Story (n = story): adds only «@meshkani.pro», centred, as the lowest element, bottom edge 12 px above the
// 280 px safe line (no number, no label — user rule). Both: the image itself always fills the frame.
import fs from 'fs'; import path from 'path'; import {createRequire} from 'module';
const require = createRequire('/home/user/ARpage/news-reel/');
const {chromium} = require('playwright');
const [, , inp, out, n, theme, inkArg] = process.argv;
const FONTS = '/home/user/ARpage/logo-motion/node_modules/@fontsource/vazirmatn/files/';
const dark = theme === 'dark', pill = theme === 'pill', story = n === 'story', H = story ? 1920 : 1350;
const ink = inkArg || (dark ? '#F3EAF8' : '#3B1F4A'), chipBg = dark ? 'rgba(255,255,255,.14)' : 'rgba(30,30,40,.10)';
const fa = s => String(s).replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]);
const html = `<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:Vaz;font-weight:500;src:url(file://${FONTS}vazirmatn-arabic-600-normal.woff2)}
@font-face{font-family:Vaz;font-weight:800;src:url(file://${FONTS}vazirmatn-arabic-800-normal.woff2)}
@font-face{font-family:VazL;font-weight:600;src:url(file://${FONTS}../../../inter/files/inter-latin-600-normal.woff2)}
html,body{margin:0;width:1080px;height:${H}px;overflow:hidden}
#bg{position:absolute;left:0;top:0;width:1080px;height:${H}px;object-fit:cover}
#sh{position:absolute;left:0;right:0;top:1582px;height:46px;display:flex;justify-content:center}
#sh span{font:600 26px VazL,Vaz,sans-serif;direction:ltr;color:${ink};${pill ? 'background:rgba(243,233,216,.93);padding:0 24px;border-radius:26px;height:46px;display:flex;align-items:center' : 'text-shadow:0 1px 8px rgba(0,0,0,.35)'}}
.row{position:absolute;top:1148px;height:52px;display:flex;align-items:center;color:${ink};font-family:Vaz;line-height:1}
#h{left:100px;font:600 24px VazL,Vaz,sans-serif;letter-spacing:.2px;direction:ltr}
${pill ? '#h,#num{background:rgba(243,233,216,.93);color:' + ink + ';padding:0 22px;border-radius:26px;height:46px;display:flex;align-items:center}' : ''}
#r{right:100px;direction:rtl;gap:18px}
#num{font:800 26px Vaz}
#lab{font:500 21px Vaz;background:${pill ? 'rgba(243,233,216,.93)' : chipBg};padding:11px 20px;border-radius:26px}
</style><img id="bg" src="file://${path.resolve(inp)}">
${story ? '<div id="sh"><span>@meshkani.pro</span></div>' : `<div class="row" id="h">@meshkani.pro</div>
<div class="row" id="r"><span id="num">${fa(n)} از ۳</span><span id="lab">تصویر مفهومی</span></div>`}`;
const f = path.resolve('/home/user/ARpage/work/_ov.html'); fs.writeFileSync(f, html);
const exe = fs.readdirSync('/opt/pw-browsers').filter(d => d.startsWith('chromium-')).map(d => `/opt/pw-browsers/${d}/chrome-linux/chrome`).find(p => fs.existsSync(p));
const b = await chromium.launch({executablePath: exe, args: ['--no-sandbox', '--allow-file-access-from-files']});
const p = await b.newPage({viewport: {width: 1080, height: H}});
await p.goto('file://' + f); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
await p.screenshot({path: out, type: 'jpeg', quality: 92});
const box = await p.evaluate(ids => ids.map(i => { const r = document.getElementById(i).getBoundingClientRect(); return [i, Math.round(r.left), Math.round(r.top), Math.round(r.right), Math.round(r.bottom)]; }), story ? ['sh'] : ['h', 'r']);
console.log(JSON.stringify(box)); await b.close();
