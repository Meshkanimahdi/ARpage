// Narration for a story reel with word timings (the on-screen text follows the voice word by word).
//   node news-reel/story_voice.mjs --dir=work/story [--target=66]
// Reads <dir>/story.json (voice + beats[].text; the spoken text is the beat text without the * and |
// markup), calls ElevenLabs TTS "with-timestamps" once per beat, trims, fits the tempo so the reel lands
// at ~60–70 s, and writes <dir>/timeline.json {lines:{id:{start,end,words:[[t0,t1]..]}}, end_start, total, start:0}
// plus <dir>/voice/trim/<id>.wav. Key: env Elevenlabs_API_KEY (audio only, never printed).
import fs from 'node:fs'; import path from 'node:path'; import crypto from 'node:crypto'; import {execFileSync} from 'node:child_process';
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const dir = path.resolve(args.dir), TARGET = +(args.target || 66), MAXTEMPO = 1.2;
const key = process.env.Elevenlabs_API_KEY || process.env.ELEVENLABS_API_KEY;
if (!key) { console.error('no ElevenLabs key in env'); process.exit(2); }
const S = JSON.parse(fs.readFileSync(path.join(dir, 'story.json'), 'utf8'));
const vdir = path.join(dir, 'voice'); fs.mkdirSync(path.join(vdir, 'trim'), {recursive: true});
const sh = (c, a) => execFileSync(c, a, {encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe']});
const spoken = t => t.replace(/\*/g, '').replace(/\s*\|\s*/g, ' ').replace(/\s+/g, ' ').trim();

async function tts(text, out) {
  if (fs.existsSync(out + '.json')) return JSON.parse(fs.readFileSync(out + '.json', 'utf8'));
  for (let i = 0; i < 3; i++) {
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${S.voice}/with-timestamps?output_format=mp3_44100_192`, {method: 'POST',
      headers: {'xi-api-key': key, 'Content-Type': 'application/json'},
      body: JSON.stringify({text, model_id: S.tts_model || 'eleven_v4', language_code: 'fa', seed: 7,
        voice_settings: {stability: 0.45, similarity_boost: 0.85, style: 0.3}})});
    if (r.ok) { const j = await r.json(); fs.writeFileSync(out, Buffer.from(j.audio_base64, 'base64')); const al = j.alignment || j.normalized_alignment; fs.writeFileSync(out + '.json', JSON.stringify(al)); return al; }
    console.error('TTS', r.status, (await r.text()).slice(0, 200)); await new Promise(z => setTimeout(z, 2000 * (i + 1)));
  }
  throw new Error('TTS failed: ' + text.slice(0, 40));
}
// word [start,end] from character alignment
function wordTimes(text, al) {
  const ch = al.characters, st = al.character_start_times_seconds, en = al.character_end_times_seconds;
  const joined = ch.join(''); let off = 0; const out = [];
  for (const w of text.split(' ')) {
    let i = joined.indexOf(w, off); if (i < 0) i = off;
    const j = Math.min(ch.length - 1, i + w.length - 1);
    out.push([st[Math.min(i, st.length - 1)], en[j]]); off = i + w.length;
  }
  return out;
}

const items = [];
for (const b of S.beats) {
  const text = spoken(b.text), hsh = crypto.createHash('sha256').update(S.voice + '|' + text).digest('hex').slice(0, 10);
  const raw = path.join(vdir, `${b.id}-${hsh}.mp3`), al = await tts(text, raw);
  const wt = wordTimes(text, al), s0 = Math.max(0, wt[0][0] - .04), s1 = wt[wt.length - 1][1] + .12;
  items.push({id: b.id, text, raw, s0, d: s1 - s0, words: wt.map(([a, c]) => [a - s0, c - s0]), pause: b.pause || 0});
}
const GAP = .16, FIRST = .3, ENDCARD = 2.4;
const speech = items.reduce((s, x) => s + x.d + x.pause, 0) + GAP * (items.length - 1);
let tempo = Math.max(1, Math.min(MAXTEMPO, (FIRST + speech + .5 + ENDCARD) / TARGET));
const lines = {}; let t = FIRST;
for (const [i, x] of items.entries()) {
  if (i) t += GAP + x.pause;
  const d = x.d / tempo; lines[x.id] = {start: +t.toFixed(3), end: +(t + d).toFixed(3), words: x.words.map(([a, c]) => [+(t + a / tempo).toFixed(3), +(t + c / tempo).toFixed(3)])};
  sh('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(x.s0), '-t', String(x.d), '-i', x.raw, '-af', `atempo=${tempo.toFixed(3)},afade=t=out:st=${(d - .05).toFixed(3)}:d=0.05`, '-ar', '48000', '-ac', '2', path.join(vdir, 'trim', `${x.id}.wav`)]);
  t += d;
}
const end_start = +(t + .5).toFixed(3), total = +(end_start + ENDCARD).toFixed(3);
fs.writeFileSync(path.join(dir, 'timeline.json'), JSON.stringify({start: 0, lines, end_start, total, endcard: [end_start, total], tempo: +tempo.toFixed(3), voice: S.voice}, null, 1));
console.log(`timeline: ${total}s (speech ${speech.toFixed(1)}s, tempo ${tempo.toFixed(3)}, ${items.length} beats)`);
if (total > 75) { console.error('too long: shorten the script (target 60–70 s)'); process.exit(3); }
