// Persian narration in Mahdi's cloned voice (ElevenLabs), one file per line, plus STT check.
// ELEVEN_KEY_FILE=key.txt node voice/generate.mjs --voice=<id> [--take=a]
// Voice per reel: alternate female/male and pick the tone that fits the news (see VOICES.md).
import fs from 'node:fs'; import path from 'node:path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const key = fs.readFileSync(process.env.ELEVEN_KEY_FILE, 'utf8').match(/^Alll:\s*(\S+)/m)[1];
const VOICE = (process.argv.find(a => a.startsWith('--voice=')) || '--voice=N7wuKHXQQ5fKd75noieq').split('=')[1], MODEL = 'eleven_v4';
const take = (process.argv.find(a => a.startsWith('--take=')) || '--take=a').split('=')[1];
const lines = fs.readFileSync(path.join(dir, 'script.txt'), 'utf8').trim().split('\n').map(l => l.split('|'));
const out = path.join(dir, take); fs.mkdirSync(out, {recursive: true});
const qc = [];
for (const [id, text] of lines) {
  const f = path.join(out, `${id}.mp3`);
  if (!fs.existsSync(f)) {
    const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${VOICE}?output_format=mp3_44100_192`, {method: 'POST',
      headers: {'xi-api-key': key, 'Content-Type': 'application/json'},
      body: JSON.stringify({text, model_id: MODEL, language_code: 'fa', seed: take === 'a' ? 7 : 1234,
        voice_settings: {stability: 0.5, similarity_boost: 0.85, style: 0.2}})});
    if (!r.ok) { console.error(id, r.status, (await r.text()).slice(0, 300)); continue; }
    fs.writeFileSync(f, Buffer.from(await r.arrayBuffer()));
  }
  const fd = new FormData(); fd.append('model_id', 'scribe_v1'); fd.append('language_code', 'fas');
  fd.append('file', new Blob([fs.readFileSync(f)]), `${id}.mp3`);
  const s = await fetch('https://api.elevenlabs.io/v1/speech-to-text', {method: 'POST', headers: {'xi-api-key': key}, body: fd});
  qc.push({id, want: text.replace(/\[[^\]]*\]\s*/g, ''), heard: s.ok ? (await s.json()).text : `STT ${s.status}`});
}
fs.writeFileSync(path.join(out, 'qc.json'), JSON.stringify(qc, null, 1));
for (const q of qc) console.log(q.id, '|', q.want, '\n   ->', q.heard);
