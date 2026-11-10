import { chromium } from 'playwright'; import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
const repo='/home/user/ARpage'; const mime={'.jpg':'image/jpeg','.html':'text/html','.woff2':'font/woff2'};
const srv=http.createServer((q,r)=>{const f=path.join(repo,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);r.end();return;}r.writeHead(200,{'Content-Type':mime[path.extname(f)]||'application/octet-stream'});r.end(d);});}).listen(0);
const V=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'}); const p=await b.newPage({viewport:{width:1080,height:1920}});
for(const v of V){ const u=`http://127.0.0.1:${srv.address().port}/news-reel/cover_real.html?`+new URLSearchParams({bg:v.bg,title:v.title,pos:v.pos,a:v.a||''});
  await p.goto(u); await p.evaluate(()=>window.ok); await p.waitForTimeout(300); await p.screenshot({path:`${v.out}`,type:'jpeg',quality:92}); console.log(v.id);}
await b.close(); srv.close();
