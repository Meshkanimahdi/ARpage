// Pronunciation test for English names in the Persian narration (user rule 2026-10-29).
// Mahdi: «نام برندها و یا اصطلاحات باید به انگلیسی بیاد… الان داره ChatGPT رو chetgpt و Pro رو Pero میخونه».
// The voice is Persian (language_code fa), so a Latin word in the text gets a Persian accent. For every Latin
// term in story.json beats (after fa_lexicon latinize) that is not yet in news-reel/pron_cache.json, this
// synthesises the term in three ways with the story's voice and keeps the one an English speech-to-text hears
// best:
//   A  Latin, language_code fa (the old way)        B  Latin, no language_code (the model picks English)
//   C  Persian respelling with diacritics (fa_lexicon PRON, e.g. چَت‌جی‌پی‌تی), language_code fa
// The winners are cached (commit pron_cache.json), and story_voice.mjs uses them: mode C replaces the term in
// the spoken text; mode B sends that beat without language_code. Also writes voice/pron_samples.mp3 (each
// winning term once) for a human listen.
//   node news-reel/pron_test.mjs --dir=work/story
// Exit 4 when a term scores below 0.75 in every mode: add a respelling to PRON or rephrase it.
import fs from 'node:fs'; import path from 'node:path'; import {execFileSync} from 'node:child_process';
import {latinize, PRON, latinTerms} from './fa_lexicon.mjs';
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const dir = path.resolve(args.dir), here = path.dirname(new URL(import.meta.url).pathname);
const key = process.env.Elevenlabs_API_KEY || process.env.ELEVENLABS_API_KEY;
if (!key) { console.error('no ElevenLabs key in env'); process.exit(2); }
const S = JSON.parse(fs.readFileSync(path.join(dir, 'story.json'), 'utf8'));
const cacheF = path.join(here, 'pron_cache.json');
const cache = fs.existsSync(cacheF) ? JSON.parse(fs.readFileSync(cacheF, 'utf8')) : {};
const out = path.join(dir, 'voice', 'pron'); fs.mkdirSync(out, {recursive: true});
const letters = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
function sim(a, b) { a = letters(a); b = letters(b); const m = a.length, n = b.length; if (!m || !n) return 0;
  let p = Array.from({length: n + 1}, (_, j) => j);
  for (let i = 1; i <= m; i++) { const c = [i]; for (let j = 1; j <= n; j++) c[j] = Math.min(p[j] + 1, c[j - 1] + 1, p[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)); p = c; }
  return 1 - p[n] / Math.max(m, n); }
async function tts(text, lang, f) {
  if (fs.existsSync(f)) return;
  const body = {text, model_id: 'eleven_v4', seed: 7, voice_settings: {stability: 0.6, similarity_boost: 0.85, use_speaker_boost: true}};
  if (lang) body.language_code = lang;
  const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${S.voice}?output_format=mp3_44100_192`, {method: 'POST',
    headers: {'xi-api-key': key, 'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  if (!r.ok) throw new Error(`TTS ${r.status} ${(await r.text()).slice(0, 200)}`);
  fs.writeFileSync(f, Buffer.from(await r.arrayBuffer()));
}
async function sttEn(f) {
  const fd = new FormData(); fd.append('model_id', 'scribe_v1'); fd.append('language_code', 'eng');
  fd.append('file', new Blob([fs.readFileSync(f)]), path.basename(f));
  const r = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {method: 'POST', headers: {'xi-api-key': key}, body: fd});
  if (!r.ok) throw new Error('STT ' + r.status); return (await r.json()).text || '';
}
const terms = [...new Set(S.beats.flatMap(b => latinTerms(latinize(b.text.replace(/\{([^|}]*)\|([^}]*)\}/g, '$2'), S.lexicon))))];
const fresh = terms.filter(t => !cache[t]), bad = [];
for (const term of fresh) {
  const slug = letters(term).slice(0, 24) || 'term';
  const tries = [['A', term, 'fa'], ['B', term, null]];
  if (PRON[term]) tries.push(['C', PRON[term], 'fa']);
  let best = null;
  for (const [mode, text, lang] of tries) {
    const f = path.join(out, `${slug}-${mode}.mp3`); await tts(text, lang, f);
    const heard = await sttEn(f), score = sim(term, heard);
    console.log(term, mode, score.toFixed(2), '->', heard);
    if (!best || score > best.score + 0.02 || (Math.abs(score - best.score) <= 0.02 && mode === 'C')) best = {mode, text, score, f};
  }
  cache[term] = {mode: best.mode, spoken: best.mode === 'C' ? best.text : term, score: +best.score.toFixed(2), voice: S.voice, date: new Date().toISOString().slice(0, 10)};
  if (best.score < 0.75) bad.push(`${term} (${best.score.toFixed(2)})`);
}
fs.writeFileSync(cacheF, JSON.stringify(cache, null, 1));
const wins = terms.map(t => path.join(out, `${letters(t).slice(0, 24) || 'term'}-${cache[t].mode}.mp3`)).filter(f => fs.existsSync(f));
if (wins.length) execFileSync('ffmpeg', ['-y', '-loglevel', 'error', ...wins.flatMap(f => ['-i', f]), '-filter_complex',
  wins.map((_, i) => `[${i}]apad=pad_dur=0.5[a${i}]`).join(';') + ';' + wins.map((_, i) => `[a${i}]`).join('') + `concat=n=${wins.length}:v=0:a=1`, path.join(dir, 'voice', 'pron_samples.mp3')]);
console.log(JSON.stringify(Object.fromEntries(terms.map(t => [t, cache[t]]))));
if (bad.length) { console.error('terms no mode pronounces well: ' + bad.join(', ') + ' → add a PRON respelling in fa_lexicon.mjs or rephrase'); process.exit(4); }
