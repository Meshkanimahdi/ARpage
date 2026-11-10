# Voice, casting and sound

For ElevenLabs specifics (models, tags, pauses, pronunciation syntax) also read the `skill-elevenlabs-tts`
skill before writing any narration.

## 1. Casting and personas (blocking)
A reel once played a daughter's line «مامان، تصادف کردم…» in the male narrator's voice. Every voice and every
image must fit who is speaking.
- **Cast list before the script:** one entry per character who speaks or is shown (narrator, the AI assistant,
  the child, the father…): gender, age (child/teen/young/middle-aged/old), role, way of talking, and for
  speakers a voice id from the library.
- **Quoted words use the speaker's own voice.** A beat that quotes a character is its own beat with
  `speaker: <name>`, voiced by that character's cast voice, never the narrator's.
- **Gender and age must match** the library entry of the voice; a child or teen needs a voice the library marks
  as child/teen; the narrator's voice is never reused for a character. The AI assistant gets its own calm,
  clearly different voice.
- **No fitting voice → no fake:** rewrite the line as the narrator's indirect speech («دخترش با گریه پرسید…»), or
  find a fitting voice and add it to the library first.
- **Delivery fits the persona:** short audio tags per character (a scared child `[whispers]`, a tired father
  `[tired]`, the AI `[calm]`).
- **Images match the cast:** the same character keeps the same age, gender, face, clothes and setting across
  every frame and on the cover; a child in the story is a child on screen.
- The final critic listens to every character line and scores `casting` (≥ 6); the voice script refuses a
  speaker with no cast entry or a mismatched voice.

## 2. Voice choice and rotation (hard rules)
- Keep a **voice library** file listing the account's voices with gender, age and a one-line character note
  (deep husky news voice, warm female, young energetic…). Build it by listing, not generating; refresh weekly.
- **Never the narrator of any of the last 12 reels** (so the library needs ≥ 13 good voices).
- **Narrator gender alternates** reel to reel (male → female → male). ID rotation alone produced four similar
  male narrators in a row.
- Fit the mood: deep/husky for serious news, warm/bright for life tips; women-focused stories get a female
  narrator.

## 3. Writing for the voice
- Spoken register, short sentences, one idea per beat, questions, a pause before the number, contrast words.
- Numbers, dates, prices and percentages as words in the target language; show the short form on screen with a
  `{shown|spoken}` pair.
- Audio tags in English, lowercase, one per bracket, where the tone turns (about every 1–2 beats), never the
  same tag twice in a row; one pause device per spot (never an ellipsis plus a pause tag).
- `stability` ≈ 0.35–0.45 (0.38 default; 0.5 sounded flat), similarity 0.85, speaker boost on; no style/speed on v4.

## 4. Pronunciation
- **Brand and product names must sound like the brand** (the voice read "ChatGPT" as "chet-GPT" and "Pro" as
  "Pero"). Write them in Latin in the spoken text, then test each term three ways before the voice run
  (Latin with the target language code; Latin with the language left to the model; a native respelling with
  diacritics) and keep the one an English speech-to-text hears best. Cache results; refuse to voice an untested
  term.
- **Native words the voice misreads:** keep a respell glossary (word → diacritized spoken form) applied to the
  TTS text only, never to on-screen text. Homographs are excluded from the glossary (they are read differently
  by context); fix them with diacritics in that one sentence.
- After every voice run, speech-to-text each take, list the words not heard (`flags.json`), fix real misreads in
  the glossary, regenerate only those beats (max 2 rounds), and commit the glossary so the fix is permanent.
- QC: best of up to 3 takes per beat by speech-to-text similarity; forced alignment for word timings.

## 5. Sound effects (hard rules)
- **Every effect matches the motion it sits on:** counter tick for counting numbers, soft sweep for a chart
  drawing, tap/click for UI, notification for a chat bubble, pop for a card, shimmer/glass ping for a reveal,
  hit/bass drop for the big number or turn, typing for typing. Never one "whoosh" on every cut.
- Assembly limits: ≤ 2 whooshes per reel (6 s apart), never the same sound twice in a row, ≤ 1 effect per
  1.2 s, no single sound over 40 % of all effects.
- **The effect set differs from each of the last 3 reels** (Jaccard similarity of effect names < 0.75); write
  the cue list per scene, never paste the last reel's.
- Library first; when nothing fits, generate **one scene soundscape per reel** with a multi-event SFX model
  (cues in order with rough times) rather than one file per effect; save good results to the library; at most
  one new audio generation a day.
- Silence between effects is good: the voice and the music carry the reel.

## 6. Mix and master (so it doesn't sound dry)
| bus | chain |
|---|---|
| voice | HPF 80 Hz · LPF 15 kHz · −2.5 dB @250 Hz · +3 dB @3.2 kHz · +2 dB shelf @9 kHz · de-ess · comp 3:1 at −20 dB · very short low room (23/41 ms) |
| music | HPF 35 Hz · −4 dB @2.8 kHz · sidechain duck 6:1 from the voice, release ~450 ms |
| SFX | motion-matched cues or one soundscape, each ≤ 0.45 |
| master | glue comp 2:1 at −14 dB · loudnorm −14 LUFS, TP −1.5 dB, LRA 9 · limiter |

- One music track per reel from the library, matched to mood and tempo, not the track of the last 3 reels;
  music under the hook (not silence), dropped for one beat at the turn, back for the end.
- Check by ear on a phone speaker: voice on top and clear, music audible but never fighting the words, no
  sibilance, no sudden loud effect.

## 7. Music under a carousel
APIs cannot attach library music to a carousel, so render each approved slide as an 8 s video child with a slow
3 % push, cutting one continuous instrumental track across them (slide k plays from k × 8 s, −16 LUFS). If a
video child errors twice, publish image children without music; never skip the post over music.
