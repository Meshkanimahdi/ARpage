// Narration for a story reel (ElevenLabs eleven_v4 + audio tags) with word timings, so the on-screen
// text can follow the voice word by word.
//   node news-reel/story_voice.mjs --dir=work/story [--tempo=1.2]
// Beat text markup (story.json → beats[].text):
//   [tag]            English v4 audio tag, spoken as delivery, never shown (e.g. [curious], [whispers])
//   *word* / *a b*   big keyword on screen (not spoken differently)
//   |                line break on screen (not spoken)
//   {shown|spoken}   show one thing, say another (numbers, dates, Latin names): {۲۰۲۵|دو هزار و بیست و پنج}
// Per beat: TTS (tags kept) → speech-to-text check (best of up to 3 takes, seed changes) → forced
// alignment of the plain text → trim → fixed brisk tempo. Writes <dir>/timeline.json and voice/trim/<id>.wav.
// Key: env Elevenlabs_API_KEY (audio only, never printed). Model: eleven_v4 (user rule).
import fs from 'node:fs'; import path from 'node:path'; import crypto from 'node:crypto'; import {execFileSync} from 'node:child_process';
import {latinize, latinTerms} from './fa_lexicon.mjs';
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const dir = path.resolve(args.dir), TEMPO = +(args.tempo || 1.2);   // the brisk pace the user approved (2026-10-21)
const key = process.env.Elevenlabs_API_KEY || process.env.ELEVENLABS_API_KEY;
if (!key) { console.error('no ElevenLabs key in env'); process.exit(2); }
const S = JSON.parse(fs.readFileSync(path.join(dir, 'story.json'), 'utf8'));
const MODEL = 'eleven_v4';
const vdir = path.join(dir, 'voice'); fs.mkdirSync(path.join(vdir, 'trim'), {recursive: true});
const sh = (c, a) => execFileSync(c, a, {encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe']});
const sq = t => t.replace(/\s+/g, ' ').trim();
// pronunciation of English names (user rule 2026-10-29): run pron_test.mjs first; its cache decides per term
const PRON_CACHE = (() => { const f = new URL('./pron_cache.json', import.meta.url); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : {}; })();
const respell = t => { for (const term of latinTerms(t).sort((a, b) => b.length - a.length)) { const c = PRON_CACHE[term];
  if (c && c.mode === 'C') t = t.split(term).join(c.spoken); } return t; };
const latinOf = t => latinTerms(latinize(t.replace(/\{([^|}]*)\|([^}]*)\}/g, '$2'), S.lexicon));
const untested = [...new Set(S.beats.flatMap(b => latinOf(b.text)).filter(x => !PRON_CACHE[x]))];
if (untested.length) { console.error('run news-reel/pron_test.mjs first; untested English terms: ' + untested.join(', ')); process.exit(5); }
// character casting (user rule 2026-11-03, RUNBOOK §00.21): a beat with `speaker` is spoken by that character's own voice.
// story.json cast: {"<speaker>": {"gender": "female|male", "age": "child|teen|young|middle_aged|old", "role": "…", "voice": "<id>"}}
// The voice must exist in audio_library.json and match the character's gender; a child or teen needs a voice whose
// library age/note says child/teen/kid/girl/boy. No such voice → write the line as the narrator's indirect speech.
const LIB = (() => { const f = new URL('./audio_library.json', import.meta.url); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')).voices : []; })();
const CAST = S.cast || {};
const castErr = [];
for (const b of S.beats.filter(b => b.speaker && b.speaker !== 'narrator')) {
  const c = CAST[b.speaker];
  if (!c) { castErr.push(`beat ${b.id}: speaker «${b.speaker}» is not in story.json cast`); continue; }
  if (!c.voice || !c.gender || !c.age) { castErr.push(`cast «${b.speaker}» needs gender, age and voice`); continue; }
  const v = LIB.find(x => x.id === c.voice);
  if (!v) { castErr.push(`cast «${b.speaker}»: voice ${c.voice} is not in audio_library.json`); continue; }
  if (v.gender && v.gender !== 'neutral' && v.gender !== c.gender) castErr.push(`cast «${b.speaker}» is ${c.gender} but voice «${v.name}» is ${v.gender}`);
  const young = /child|kid|girl|boy|teen|children/i.test(`${v.age} ${v.name} ${v.note}`);
  if (['child', 'teen'].includes(c.age) && !young) castErr.push(`cast «${b.speaker}» is a ${c.age} but voice «${v.name}» is not a child/teen voice: pick one, or make the line the narrator's indirect speech`);
  if (!['child', 'teen'].includes(c.age) && v.age && c.age !== v.age && !(c.age === 'young' && v.age === 'middle_aged')) castErr.push(`cast «${b.speaker}» is ${c.age} but voice «${v.name}» is ${v.age}`);
  if (c.voice === S.voice) castErr.push(`cast «${b.speaker}» uses the narrator's voice: a character needs its own voice`);
}
if (castErr.length) { console.error('casting (RUNBOOK §00.21):\n  ' + castErr.join('\n  ')); process.exit(6); }
const voiceOf = b => (b.speaker && b.speaker !== 'narrator' && CAST[b.speaker]?.voice) || S.voice;
// Persian words the voice misreads (news-reel/fa_respell.json, user rule 2026-11-02): diacritics, TTS text only
const FA_RESPELL = (() => { const f = new URL('./fa_respell.json', import.meta.url); return fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')).words : {}; })();
const faRespell = t => { for (const [w, s] of Object.entries(FA_RESPELL).sort((a, b) => b[0].length - a[0].length)) if (w !== s)
  t = t.replace(new RegExp(`(?<![\\p{L}\\p{M}])${w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(?![\\p{L}\\p{M}])`, 'gu'), s); return t; };
const ttsText = t => faRespell(respell(withTags(t)));
const langFor = t => latinOf(t).some(x => PRON_CACHE[x]?.mode === 'B') ? null : 'fa';
const withTags = t => sq(latinize(t.replace(/\[icon:[^\]]*\]/g, '').replace(/\{([^|}]*)\|([^}]*)\}/g, '$2').replace(/\*/g, '').replace(/\s*\|\s*/g, ' '), S.lexicon));
const plain = t => sq(withTags(t).replace(/\[[^\]]*\]/g, ''));
const shownText = t => sq(t.replace(/\[icon:[^\]]*\]/g, '').replace(/\{([^|}]*)\|([^}]*)\}/g, '$1').replace(/\[[^\]]*\]/g, '').replace(/\*/g, '').replace(/\s*\|\s*/g, ' '));   // STT often writes numbers as digits
const norm = s => s.toLowerCase().replace(/[0-9]/g, d => '۰۱۲۳۴۵۶۷۸۹'[d]).replace(/[ً-ٰٟ‌\s.,،؛:!?؟«»"'()\-–—…]/g, '').replace(/ي/g, 'ی').replace(/ك/g, 'ک');
function sim(a, b) { a = norm(a); b = norm(b); const m = a.length, n = b.length; if (!m || !n) return 0;
  let p = Array.from({length: n + 1}, (_, j) => j);
  for (let i = 1; i <= m; i++) { const c = [i]; for (let j = 1; j <= n; j++) c[j] = Math.min(p[j] + 1, c[j - 1] + 1, p[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); p = c; }
  return 1 - p[n] / Math.max(m, n); }
async function retry(fn, what) { for (let i = 0; i < 3; i++) { try { return await fn(); } catch (e) { console.error(what, String(e).slice(0, 200)); await new Promise(z => setTimeout(z, 2500 * (i + 1))); } } throw new Error(what + ' failed'); }

async function tts(text, seed, out, lang = 'fa', voice = S.voice) {
  if (fs.existsSync(out)) return;
  await retry(async () => {
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_192`, {method: 'POST',
      headers: {'xi-api-key': key, 'Content-Type': 'application/json'},
      body: JSON.stringify({text, model_id: MODEL, ...(lang ? {language_code: lang} : {}), seed,
        voice_settings: {stability: S.stability ?? 0.38, similarity_boost: 0.85, use_speaker_boost: true}})});
    if (!r.ok) throw new Error(`TTS ${r.status} ${(await r.text()).slice(0, 200)}`);
    fs.writeFileSync(out, Buffer.from(await r.arrayBuffer()));
  }, 'tts');
}
async function stt(f) {
  return retry(async () => { const fd = new FormData(); fd.append('model_id', 'scribe_v1'); fd.append('language_code', 'fas');
    fd.append('file', new Blob([fs.readFileSync(f)]), path.basename(f));
    const r = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {method: 'POST', headers: {'xi-api-key': key}, body: fd});
    if (!r.ok) throw new Error('STT ' + r.status); return (await r.json()).text; }, 'stt');
}
async function align(f, text) {
  const cache = f + '.align.json'; if (fs.existsSync(cache)) return JSON.parse(fs.readFileSync(cache, 'utf8'));
  return retry(async () => { const fd = new FormData(); fd.append('text', text); fd.append('file', new Blob([fs.readFileSync(f)]), path.basename(f));
    const r = await fetch('https://api.elevenlabs.io/v1/forced-alignment', {method: 'POST', headers: {'xi-api-key': key}, body: fd});
    if (!r.ok) throw new Error('align ' + r.status + ' ' + (await r.text()).slice(0, 200));
    const j = await r.json(); fs.writeFileSync(cache, JSON.stringify(j)); return j; }, 'align');
}

const items = [], qc = [];
for (const b of S.beats) {
  const spoken = ttsText(b.text), lang = langFor(b.text), ptxt = plain(b.text), pw = ptxt.split(' ');
  const hsh = crypto.createHash('sha256').update(voiceOf(b) + '|' + MODEL + '|' + lang + '|' + spoken).digest('hex').slice(0, 10);
  let best = null;
  for (let take = 0; take < 3; take++) {        // up to 3 takes, keep the clearest
    const f = path.join(vdir, `${b.id}-${hsh}-${take}.mp3`); await tts(spoken, 7 + take * 101, f, lang, voiceOf(b));
    const heard = await stt(f), score = Math.max(sim(ptxt, heard), sim(ptxt, latinize(heard, S.lexicon)), sim(shownText(b.text), heard));   // STT may write Latin names in Persian
    if (!best || score > best.score) best = {f, heard, score};
    if (score >= 0.9) break;
  }
  qc.push({id: b.id, spoken, heard: best.heard, score: +best.score.toFixed(3), file: path.basename(best.f)});
  const al = await align(best.f, ptxt);
  let ws = (al.words || []).filter(w => (w.text || '').trim()).map(w => [w.start, w.end]);
  if (ws.length !== pw.length) {            // keep one timing per written word
    const tot = al.words?.length ? al.words[al.words.length - 1].end : 1;
    if (ws.length > pw.length) ws = ws.slice(0, pw.length);
    while (ws.length < pw.length) { const last = ws[ws.length - 1] || [0, 0]; ws.push([last[1], Math.min(tot, last[1] + .2)]); }
  }
  const s0 = Math.max(0, ws[0][0] - .04), s1 = ws[ws.length - 1][1] + .12;
  items.push({id: b.id, f: best.f, s0, d: s1 - s0, words: ws.map(([a, c]) => [a - s0, c - s0]), pause: b.pause || 0});
}
fs.writeFileSync(path.join(vdir, 'qc.json'), JSON.stringify(qc, null, 1));
// word-level flags: written words the speech-to-text did not hear → likely misread; fix in fa_respell.json / PRON
const flags = qc.map(q => { const heard = ' ' + norm(q.heard) + ' ';
  const miss = plain(S.beats.find(b => b.id === q.id).text).split(' ').filter(w => norm(w).length > 1 && !heard.includes(norm(w)));
  return {id: q.id, score: q.score, missed_words: miss}; }).filter(x => x.missed_words.length);
fs.writeFileSync(path.join(vdir, 'flags.json'), JSON.stringify(flags, null, 1));
if (flags.length) console.log('possible misread words (voice/flags.json):', flags.map(f => f.id + ': ' + f.missed_words.join('، ')).join(' | '));
for (const q of qc) if (q.score < 0.8) console.log('!!', q.id, q.score, '|', q.spoken, '\n   ->', q.heard);

const GAP = .16, FIRST = .3, ENDCARD = 2.4, tempo = TEMPO, lines = {};
let t = FIRST;
for (const [i, x] of items.entries()) {
  if (i) t += GAP + x.pause;
  const d = x.d / tempo;
  lines[x.id] = {start: +t.toFixed(3), end: +(t + d).toFixed(3), words: x.words.map(([a, c]) => [+(t + a / tempo).toFixed(3), +(t + c / tempo).toFixed(3)])};
  sh('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(x.s0), '-t', String(x.d), '-i', x.f, '-af', `atempo=${tempo.toFixed(3)},afade=t=out:st=${Math.max(0, d - .05).toFixed(3)}:d=0.05`, '-ar', '48000', '-ac', '2', path.join(vdir, 'trim', `${x.id}.wav`)]);
  t += d;
}
const end_start = +(t + .5).toFixed(3), total = +(end_start + ENDCARD).toFixed(3);
fs.writeFileSync(path.join(dir, 'timeline.json'), JSON.stringify({start: 0, lines, end_start, total, endcard: [end_start, total], tempo, voice: S.voice, model: MODEL}, null, 1));
console.log(`timeline: ${total}s (${items.length} beats, tempo ${tempo}, min STT ${Math.min(...qc.map(q => q.score)).toFixed(2)})`);
const MAXLEN = Math.min(152, (S.target_len || 150) + 6);   // length follows the topic (user rule 2026-11-02): 30–150 s, set story.json → target_len
if (total > MAXLEN) { console.error(`too long: ${total}s > ${MAXLEN}s (story.json target_len ${S.target_len || 150}, hard max 150 s, RUNBOOK §4.0)`); process.exit(3); }
if (qc.some(q => q.score < 0.8)) { console.error('speech-to-text below 0.8 on some beats (voice/qc.json): respell with diacritics or rephrase'); process.exit(4); }
