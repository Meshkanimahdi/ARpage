// Narration takes from voice/script.txt via ElevenLabs, plus speech-to-text QC.
// Usage: ELEVEN_KEY_FILE=key.txt node voice/generate.mjs --voice=<id> [--model=eleven_v4] [--ids=V01,V02] [--takes=a,b] [--dir=voice/takes] [--qc]
import fs from 'node:fs';
import path from 'node:path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const args = Object.fromEntries(process.argv.slice(2).map(a => { const [k, ...v] = a.replace(/^--/, '').split('='); return [k, v.join('=') || true]; }));
const raw = fs.readFileSync(process.env.ELEVEN_KEY_FILE, 'utf8');
const key = (raw.match(/^Alll:\s*(\S+)/m) || raw.match(/(sk_\w+)/))[1];
const voice = args.voice, model = args.model || 'eleven_v4';
const outDir = path.resolve(args.dir || path.join(dir, 'takes')); fs.mkdirSync(outDir, {recursive: true});
const takes = (args.takes || 'a').split(',');
const want = args.ids ? new Set(args.ids.split(',')) : null;
const lines = fs.readFileSync(path.join(dir, 'script.txt'), 'utf8').split('\n').filter(l => /^V\d+\|/.test(l)).map(l => { const [id, slot, text] = l.split('|'); return {id, slot, text}; }).filter(l => !want || want.has(l.id));
const SEED = {a: 7, b: 1234, c: 98765};
async function tts(ln, take) {
  const out = path.join(outDir, `${ln.id}_${take}.mp3`);
  if (fs.existsSync(out)) return out;
  const body = {text: ln.text, model_id: model, voice_settings: {stability: 0.5, similarity_boost: 0.85}, seed: SEED[take] ?? 7};
  if (!model.startsWith('eleven_multilingual')) body.language_code = 'fa';
  for (let i = 0; i < 3; i++) {
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_128`, {method: 'POST', headers: {'xi-api-key': key, 'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    if (r.ok) { fs.writeFileSync(out, Buffer.from(await r.arrayBuffer())); return out; }
    console.error(ln.id, take, r.status, (await r.text()).slice(0, 200));
    await new Promise(s => setTimeout(s, 2000 * (i + 1)));
  }
}
async function stt(file) {
  const fd = new FormData(); fd.append('model_id', 'scribe_v1'); fd.append('language_code', 'fas');
  fd.append('file', new Blob([fs.readFileSync(file)]), path.basename(file));
  const r = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {method: 'POST', headers: {'xi-api-key': key}, body: fd});
  return r.ok ? (await r.json()).text : `STT ${r.status}`;
}
const jobs = []; for (const ln of lines) for (const t of takes) jobs.push([ln, t]);
const results = [];
for (let i = 0; i < jobs.length; i += 6) await Promise.all(jobs.slice(i, i + 6).map(async ([ln, t]) => { const f = await tts(ln, t); if (f && args.qc) results.push({id: ln.id, take: t, want: ln.text, heard: await stt(f)}); }));
if (args.qc) { results.sort((a, b) => (a.id + a.take).localeCompare(b.id + b.take)); fs.writeFileSync(path.join(outDir, `qc-${model}.json`), JSON.stringify(results, null, 1)); results.forEach(r => console.log(r.id, r.take, '|', r.want.replace(/\[[^\]]*\]\s*/g, ''), '||', r.heard)); }
console.log('done', jobs.length, 'takes');
