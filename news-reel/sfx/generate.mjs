// Music bed + transition effects for the news reel (ElevenLabs, audio key line only).
import fs from 'node:fs'; import path from 'node:path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const key = fs.readFileSync(process.env.ELEVEN_KEY_FILE, 'utf8').match(/^Alll:\s*(\S+)/m)[1];
const H = {'xi-api-key': key, 'Content-Type': 'application/json'};
async function sfx(id, text, dur) {
  const f = path.join(dir, `${id}.mp3`); if (fs.existsSync(f)) return;
  const r = await fetch('https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_192', {method: 'POST', headers: H,
    body: JSON.stringify({text, duration_seconds: dur, prompt_influence: 0.6})});
  if (!r.ok) return console.error(id, r.status, (await r.text()).slice(0, 300));
  fs.writeFileSync(f, Buffer.from(await r.arrayBuffer())); console.log('ok', id);
}
async function music() {
  const f = path.join(dir, 'music.mp3'); if (fs.existsSync(f)) return;
  const r = await fetch('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192', {method: 'POST', headers: H,
    body: JSON.stringify({prompt: 'Modern tech news underscore, confident and curious, pulsing synth bass, light electronic percussion, clean minimal, steady 110 bpm, no vocals, suitable under a spoken narration', music_length_ms: 27000, force_instrumental: true})});
  if (!r.ok) return console.error('music', r.status, (await r.text()).slice(0, 400));
  fs.writeFileSync(f, Buffer.from(await r.arrayBuffer())); console.log('ok music');
}
await music();
await sfx('whoosh', 'fast clean cinematic whoosh transition, airy swish, short', 0.9);
await sfx('hit', 'soft deep cinematic hit with short tonal shimmer, tech news accent, clean', 1.6);
await sfx('tick', 'four quick soft digital UI pops in sequence, clean, subtle', 1.2);
await sfx('riser', 'short reverse swell riser into silence, airy tech, subtle', 1.5);
