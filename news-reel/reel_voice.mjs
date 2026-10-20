// Narration for the daily reel: one ElevenLabs voice per news (+ the closing line in the last voice),
// speech-to-text check, silence trim, tempo fit and the timeline the template and the mixer read.
//   node news-reel/reel_voice.mjs --dir=work/reel-2026-10-20 [--budget=26]
// Key: env Elevenlabs_API_KEY / ELEVENLABS_API_KEY (audio only; never used for images, never printed).
import fs from 'node:fs'; import path from 'node:path'; import crypto from 'node:crypto'; import {execFileSync} from 'node:child_process';
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const dir = path.resolve(args.dir); const BUDGET = +(args.budget || 26), MAXLEN = 60.5, MAXTEMPO = 1.25;
const key = process.env.Elevenlabs_API_KEY || process.env.ELEVENLABS_API_KEY
  || (process.env.ELEVEN_KEY_FILE && fs.readFileSync(process.env.ELEVEN_KEY_FILE, 'utf8').match(/^Alll:\s*(\S+)/m)[1]);
if (!key) { console.error('no ElevenLabs key in env'); process.exit(2); }
const spec = JSON.parse(fs.readFileSync(path.join(dir, 'spec.json'), 'utf8'));
const vdir = path.join(dir, 'voice'); fs.mkdirSync(path.join(vdir, 'trim'), {recursive: true});
const sh = (cmd, a) => execFileSync(cmd, a, {encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe']});
const dur = f => +sh('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).trim();
const clean = s => s.replace(/\[[^\]]*\]\s*/g, '');
const norm = s => clean(s).replace(/[ً-ٰٟ‌\s.,،؛:!?؟«»"'()\-–—]/g, '').replace(/ي/g, 'ی').replace(/ك/g, 'ک');
function sim(a, b) { a = norm(a); b = norm(b); const m = a.length, n = b.length; if (!m || !n) return 0;
  let prev = Array.from({length: n + 1}, (_, j) => j);
  for (let i = 1; i <= m; i++) { const cur = [i]; for (let j = 1; j <= n; j++) cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); prev = cur; }
  return 1 - prev[n] / Math.max(m, n); }

async function tts(text, voice, out) {
  if (fs.existsSync(out)) return;
  for (let i = 0; i < 3; i++) {
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_192`, {method: 'POST',
      headers: {'xi-api-key': key, 'Content-Type': 'application/json'},
      body: JSON.stringify({text, model_id: spec.tts_model || 'eleven_v4', language_code: 'fa', seed: 7,
        voice_settings: {stability: 0.5, similarity_boost: 0.85, style: 0.2}})});
    if (r.ok) { fs.writeFileSync(out, Buffer.from(await r.arrayBuffer())); return; }
    console.error('TTS', r.status, (await r.text()).slice(0, 200)); await new Promise(z => setTimeout(z, 2000 * (i + 1)));
  }
  throw new Error('TTS failed for ' + path.basename(out));
}
async function stt(f) {
  const fd = new FormData(); fd.append('model_id', 'scribe_v1'); fd.append('language_code', 'fas');
  fd.append('file', new Blob([fs.readFileSync(f)]), path.basename(f));
  const s = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {method: 'POST', headers: {'xi-api-key': key}, body: fd});
  return s.ok ? (await s.json()).text : `STT ${s.status}`;
}

// 1) synthesize every line (cached by voice + text, so a rerun only pays for changed lines)
const groups = spec.news.map(n => ({voice: n.voice, lines: n.lines.map(l => ({...l}))}));
if (spec.end_line) groups[groups.length - 1].lines.push({id: 'END', text: spec.end_line, endcard: true});
const qc = [];
for (const g of groups) for (const l of g.lines) {
  const hsh = crypto.createHash('sha256').update(g.voice + '|' + l.text).digest('hex').slice(0, 10);
  l.raw = path.join(vdir, `${l.id}-${hsh}.mp3`); await tts(l.text, g.voice, l.raw);
  const heard = await stt(l.raw), score = sim(l.text, heard);
  qc.push({id: l.id, want: clean(l.text), heard, score: +score.toFixed(3)});
  // 2) trim leading/trailing silence
  l.trim = path.join(vdir, `${l.id}-trim.wav`);
  sh('ffmpeg', ['-y', '-loglevel', 'error', '-i', l.raw, '-af', 'silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse', '-ar', '48000', '-ac', '2', l.trim]);
  l.d = dur(l.trim);
}
fs.writeFileSync(path.join(vdir, 'qc.json'), JSON.stringify(qc, null, 1));
for (const q of qc) console.log(q.score < 0.8 ? '!! ' : '   ', q.id, q.score, '|', q.want, '\n      ->', q.heard);

// 3) tempo per news so each fits its budget, then lay the lines out
const GAP = .1, FIRST = 3.9, DIV = 1.45;
const speech = g => g.lines.filter(l => !l.endcard).reduce((s, l) => s + l.d + (l.pause || 0), 0) + GAP * (g.lines.filter(l => !l.endcard).length - 1);
let tempo = groups.map(g => clamp(speech(g) / BUDGET, 1.0, 9));
function layout() {
  const lines = {}, news = [], dividers = []; let t = FIRST, endcard = null;
  groups.forEach((g, gi) => {
    if (gi > 0) { dividers.push([t + .35, t + DIV]); t += DIV; }
    const st = t;
    for (const [i, l] of g.lines.entries()) {
      const d = l.d / tempo[gi];
      if (l.endcard) { t += .25; lines[l.id] = [t, t + d]; endcard = [t - .15, t + d + .9]; t += d; continue; }
      if (i > 0) t += GAP + (l.pause || 0);
      lines[l.id] = [+t.toFixed(3), +(t + d).toFixed(3)]; t += d;
    }
    news.push({start: st, end: Math.max(...g.lines.filter(l => !l.endcard).map(l => lines[l.id][1])), voice: g.voice});
  });
  if (!endcard) endcard = [t + .2, t + 2.6];
  return {lines, news, dividers, endcard, total: endcard[1]};
}
function clamp(x, a, b) { return Math.min(b, Math.max(a, x)); }
let tl = layout();
while (tl.total > MAXLEN && Math.max(...tempo) < MAXTEMPO) { tempo = tempo.map(x => Math.min(MAXTEMPO, x + .01)); tl = layout(); }
const bad = tempo.map((x, i) => x > MAXTEMPO ? `news ${i + 1}: ${speech(groups[i]).toFixed(1)}s of speech needs tempo ${x.toFixed(2)} (max ${MAXTEMPO}); shorten its lines` : '').filter(Boolean);
if (tl.total > MAXLEN) bad.push(`reel would be ${tl.total.toFixed(1)}s (max ${MAXLEN}); shorten the script`);
if (bad.length) { console.error(bad.join('\n')); process.exit(3); }
// 4) final per-line audio at the chosen tempo
groups.forEach((g, gi) => { for (const l of g.lines) sh('ffmpeg', ['-y', '-loglevel', 'error', '-i', l.trim, '-af', `atempo=${tempo[gi].toFixed(3)}`, path.join(vdir, 'trim', `${l.id}.wav`)]); });
tl.tempo = tempo.map(x => +x.toFixed(3));
fs.writeFileSync(path.join(dir, 'timeline.json'), JSON.stringify(tl, null, 1));
console.log(`timeline: ${tl.total.toFixed(2)}s, tempo ${tl.tempo.join(' / ')}, news ${tl.news.map(n => (n.end - n.start).toFixed(1) + 's').join(' + ')}`);
if (qc.some(q => q.score < 0.8)) { console.error('speech-to-text check below 0.8 on some lines (see voice/qc.json): listen, then rewrite or respell those lines'); process.exit(4); }
