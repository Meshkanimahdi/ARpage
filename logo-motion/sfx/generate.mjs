// Sound effects for the logo motion via ElevenLabs sound generation.
// Usage: ELEVEN_KEY_FILE=key.txt node sfx/generate.mjs   (uses the "Alll" key line, never the image-only key)
import fs from 'node:fs';
import path from 'node:path';
const dir = path.dirname(new URL(import.meta.url).pathname);
const raw = fs.readFileSync(process.env.ELEVEN_KEY_FILE, 'utf8');
const key = raw.match(/^Alll:\s*(\S+)/m)[1];
export const CUES = [
  {id: 'streams', at: 0.0, dur: 1.8, vol: 0.8, text: 'futuristic digital data streams whooshing inward and converging to the center, airy high-tech swooshes, clean, no music'},
  {id: 'reveal', at: 0.9, dur: 1.4, vol: 0.9, text: 'smooth premium glassy synth swipe reveal rising, sleek futuristic logo draw-on sound, clean'},
  {id: 'impact', at: 2.0, dur: 2.6, vol: 1.0, text: 'deep cinematic sub bass boom impact with a bright crystalline shimmer tail, premium tech logo hit, clean'},
  {id: 'ping', at: 2.55, dur: 0.8, vol: 0.55, text: 'tiny soft digital sonar ping blip, clean UI notification, short'},
  {id: 'shine', at: 2.8, dur: 1.0, vol: 0.6, text: 'soft bright light gleam shimmer sweep, sparkle swish across a surface, subtle'},
  {id: 'type', at: 3.7, dur: 1.4, vol: 0.45, text: 'subtle soft futuristic UI text appearing, gentle digital ticks and blips, very light'},
  {id: 'pad', at: 3.2, dur: 2.8, vol: 0.4, text: 'warm airy ambient synth pad swell then gentle fade out, calm tech atmosphere, no melody'},
];
if (process.argv[1].endsWith('generate.mjs')) {
  for (const c of CUES) {
    const out = path.join(dir, `${c.id}.mp3`);
    if (fs.existsSync(out)) continue;
    const r = await fetch('https://api.elevenlabs.io/v1/sound-generation?output_format=mp3_44100_192', {method: 'POST',
      headers: {'xi-api-key': key, 'Content-Type': 'application/json'},
      body: JSON.stringify({text: c.text, duration_seconds: c.dur, prompt_influence: 0.6})});
    if (!r.ok) { console.error(c.id, r.status, (await r.text()).slice(0, 300)); continue; }
    fs.writeFileSync(out, Buffer.from(await r.arrayBuffer())); console.log('ok', c.id);
  }
  fs.writeFileSync(path.join(dir, 'cues.json'), JSON.stringify(CUES, null, 1));
}
