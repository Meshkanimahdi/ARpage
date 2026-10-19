// Generates one narration take per line of voice/script.txt with ElevenLabs.
// Usage: ELEVEN_KEY_FILE=/path/key.txt ELEVEN_VOICE_ID=<voice id> node voice/generate.mjs [--model=eleven_v3]
import fs from 'node:fs';
import path from 'node:path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const args = Object.fromEntries(process.argv.slice(2).map(a => a.replace(/^--/, '').split('=')));
const raw = fs.readFileSync(process.env.ELEVEN_KEY_FILE, 'utf8');
const key = (raw.match(/^Alll:\s*(\S+)/m) || raw.match(/(sk_\w+)/))[1];
const voice = process.env.ELEVEN_VOICE_ID;
if (!voice) { console.error('Set ELEVEN_VOICE_ID to the cloned voice id'); process.exit(1); }
const model = args.model || 'eleven_v3';
const lines = fs.readFileSync(path.join(dir, 'script.txt'), 'utf8').split('\n').filter(l => /^V\d+\|/.test(l)).map(l => { const [id, slot, text] = l.split('|'); return {id, slot, text}; });
for (const ln of lines) {
  const out = path.join(dir, `${ln.id}.mp3`);
  if (fs.existsSync(out)) continue;
  const r = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_128`, {
    method: 'POST', headers: {'xi-api-key': key, 'Content-Type': 'application/json'},
    body: JSON.stringify({text: ln.text, model_id: model, language_code: 'fa', voice_settings: {stability: 0.5, similarity_boost: 0.8}, seed: 7})
  });
  if (!r.ok) { console.error(ln.id, r.status, await r.text()); continue; }
  fs.writeFileSync(out, Buffer.from(await r.arrayBuffer()));
  console.log('ok', ln.id);
}
