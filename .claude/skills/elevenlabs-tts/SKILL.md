---
name: "skill-elevenlabs-tts"
description: "Write, tag and generate ElevenLabs speech (v4, v3, Multilingual v2, Flash): model and voice choice, settings, audio tags, pauses, pronunciation, normalization, dialogue, multi-take QC."
---

# ElevenLabs Text-to-Speech: best practices

Use this whenever a script is written for an ElevenLabs voice, a TTS/dialogue request is prepared, or a take sounds wrong (bad pause, mispronounced word, flat emotion, number read wrong). It covers the official best-practices guide (elevenlabs.io/docs, TTS best practices, Eleven v4, models, Text to Dialogue, TTS API reference; checked 2026-10-06) plus the production workflow proven on the Mirror films.

The docs change often (v4 is new and still "under development"). Before a big batch, re-check the models page if something behaves differently from this file.

## 1. Pick the model first
Everything else (tags, SSML, pauses, pronunciation) depends on the model.

| Model ID | Use for | Max chars / request | Audio tags | SSML break / phoneme |
|---|---|---|---|---|
| `eleven_v4` | Highest quality, most emotive; narration, ads, films, dialogue | 10,000 | Yes | No |
| `eleven_v4_turbo` | Same expressiveness, low latency; agents and live voice | 10,000 | Yes | No |
| `eleven_v3` | Previous expressive generation (still available) | 5,000 | Yes | No |
| `eleven_v3_conversational` | Real-time v3 (~280 ms) | n/a | Yes | No |
| `eleven_multilingual_v2` | Most stable on long-form; best at reading numbers itself; 29 languages | 10,000 | No | `<break>` yes |
| `eleven_flash_v2_5` | Cheapest and fastest (~75 ms), 32 languages | 40,000 | No | `<break>` yes |
| `eleven_flash_v2` | English only, fastest | 30,000 | No | `<break>` + `<phoneme>` |

Rules of thumb:
- Expressive storytelling, film or pitch narration, emotional lines: `eleven_v4` (or `eleven_v3` when an existing project's voice and takes were built on v3; v4 clones sound noticeably different from v3 clones).
- Real-time agent: `eleven_v4_turbo`, or Flash when latency and cost matter most.
- Very long, flat, number-heavy reading: `eleven_multilingual_v2`.
- Turbo v2/v2.5 are equivalent to Flash but slower; use Flash.

## 2. Pick the voice
- A delivery that already exists in the voice's training data (whispering, shouting, a calm narrator) is far easier to get than one that does not. Match tags to the voice: a serious corporate voice will fight playful tags.
- v4 follows tags outside the training data better than older models, but results may still be weaker.
- Professional Voice Clones are not fully optimized for v3; use v4 for PVCs. Instant clones need 1–2 minutes of clean audio in one consistent speaking style; noise and distortion are reproduced faithfully by v4.
- v4 cross-language change (by design): speaking a different language from the clone gives fluent native-sounding speech rather than carrying the source accent. Same-language keeps the accent. There is no toggle yet.
- Voices made with Voice Design work on v4 but can be less performative.
- Re-test key voices periodically; model behaviour shifts as v4 training improves.

## 3. Settings (API: `POST /v1/text-to-speech/{voice_id}`)
| Parameter | Range / default | Notes |
|---|---|---|
| `voice_settings.stability` | 0–1, default 0.5 | Lower = more expressive and varied, higher = fixed baseline. On v3 the UI exposes three steps: 0.0 Creative (most emotional, can hallucinate), 0.5 Natural (balanced, the default to start with), 1.0 Robust (very stable, ignores many tags). |
| `voice_settings.similarity_boost` | 0–1, default 0.75 | Closeness to the reference voice. |
| `voice_settings.style` | default 0 | Not available on v4. |
| `voice_settings.speed` | 0.7–1.2, default 1.0 | Not available on v4; ignored by v3 in practice. Use it on v2/Flash. For v3/v4 change pace with text and tags instead (see 4.4). |
| `use_speaker_boost` | default true | |
| `seed` | 0–4294967295 | Reproducible takes; change it to get a different take. |
| `previous_text` / `next_text`, `previous_request_ids` / `next_request_ids` (max 3) | | Continuity of prosody when a long script is split into several requests. |
| `pronunciation_dictionary_locators` | max 3 | See 4.2. |
| `apply_text_normalization` | `auto` / `on` / `off`, default auto | Flash v2.5 has it off unless the plan enables it, so normalize the text yourself (4.5). |
| `language_code` | ISO 639-1 | Not supported on Multilingual v2. |
| `output_format` (query) | default `mp3_44100_128` | MP3, Opus, PCM, WAV, μ-law, A-law. |

## 4. Writing the text

### 4.1 Pauses
- v2 / Flash: `<break time="1.5s" />`, up to 3 s. Use few per generation; many break tags make the voice speed up or add noise and artifacts.
- v3 / v4: SSML break tags are NOT supported. Use:
  - punctuation: full stops, commas, ellipses `…` (pause plus weight), dashes `—` (less consistent);
  - line and paragraph structure;
  - pause-style tags such as `[pause]`, `[short pause]`, `[long pause]`. These are not in the official tag list but worked reliably on v3 in the Mirror pitch film; test them on the chosen voice.
- Use ONE pause device per spot. An ellipsis followed by a pause tag (`… [pause]`) often makes the gap far too long and breaks the flow. Where the text already has `…`, let the ellipsis make the pause; use a pause tag only after a full stop, comma or colon.
- Never stack long silences inside one request to fake timing. If exact silence matters (video sync), generate the lines separately and place them in the edit.

### 4.2 Pronunciation
- v4: write IPA between forward slashes inside the sentence: `The term "/ˌbaɪoʊˈkemɪstri/" refers to…`. Include stress marks. Results still vary by voice and phrase; test important words before production.
- v2: SSML phoneme tags (compatible with `eleven_flash_v2`), one word per tag, CMU Arpabet recommended over IPA, with stress digits:
  ```xml
  <phoneme alphabet="cmu-arpabet" ph="M AE1 D IH0 S AH0 N">Madison</phoneme>
  ```
- Alias tags (any model, via dictionaries): `<lexeme><grapheme>Claughton</grapheme><alias>Cloffton</alias></lexeme>`. Matching is case-sensitive and only the first replacement is used.
- Pronunciation dictionaries: `.pls` (XML) files with phoneme or alias entries, uploaded in project settings or via API, attached with `pronunciation_dictionary_locators`.
- Cheapest fix that always works: respell the word the way it should sound (or, in Persian, add diacritics to the one wrong syllable).

### 4.3 Audio tags (v3, v4, v4 Turbo, Text to Dialogue)
Put the tag in square brackets right before the words it should colour. Tags change delivery, not the voice. Free-form descriptive tags work, so the lists below are a starting point, not a limit.
- Voice and emotion: `[laughs]`, `[laughs harder]`, `[starts laughing]`, `[wheezing]`, `[whispers]`, `[sighs]`, `[exhales]`, `[sarcastic]`, `[curious]`, `[excited]`, `[crying]`, `[snorts]`, `[mischievously]`.
- Delivery and pace (v4 examples): `[casual]`, `[measured]`, `[ecstatic]`, `[quietly curious]`, `[under his breath]`, `[quick, light, playful pace]`, `[gradually building energy]`, `[quiet, measured narration]`.
- Dialogue examples: `[excitedly]`, `[curiously]`, `[impressed]`, `[dramatically]`, `[giggling]`, `[with genuine belly laugh]`, `[delighted]`, `[amazed]`, `[warmly]`.
- Sound effects: `[gunshot]`, `[applause]`, `[clapping]`, `[explosion]`, `[swallows]`, `[gulps]`, environment such as `[leaves rustling]`.
- Experimental: `[strong French accent]` (any `[strong X accent]`), `[sings]`, `[woo]`.

How to use them well:
- Keep tags short and direct. Single words (`[whispers]`, `[tender]`, `[warm]`, `[firm]`) or very short pairs (`[quietly amazed]`) respond more consistently on v4 than long descriptions (`[soft smile in the voice]`, `[gradually building energy]`). One descriptor per bracket is the default; avoid comma lists inside one bracket.
- Write tags in lowercase. Capitalisation changes how English is read (capitals add emphasis, all-caps words may be shouted or spelled out), so keep tags lowercase and use capitals in English text only on purpose.
- Do not repeat the same tag back to back; a tone holds until the next tag.
- Change the tag where the emotion actually turns, roughly one direction per sentence or clause; tagging every word flattens the effect.
- Tags must fit the voice and the text. A sad line tagged `[excited]` gives a confused read.
- Always write tags in English, even when the text is Persian or another language.
- Write `[emphatically]` in full; for energetic sections avoid calming tags (`[softly]`, `[slowly]`, `[calmly]`).

### 4.4 Emotion and pacing without tags
- Narrative context steers emotion: `"You're leaving?" she asked, her voice trembling with sadness.` The narration is spoken too, so cut it in the edit or prefer tags when only the line is wanted.
- Pacing comes from the writing: short sentences and ellipses slow it (`"I… I thought you'd understand," he said…`), long flowing clauses speed it up.
- Punctuation (v3/v4): ellipses add weight and pause, CAPITALS add emphasis to a word, normal punctuation gives natural rhythm. Use capitals sparingly and never by accident: in English text, check product names and acronyms (`MIRROR` reads differently from `Mirror`; `MVP` is spelled out).
- Older v3 guidance: very short prompts (under ~250 characters) are less consistent; give the model a full sentence or two of context.

### 4.5 Text normalization
Smaller models misread numbers and symbols (Flash v2.5 reads "$1,000,000" as "one thousand thousand dollars"; Multilingual v2 gets it right). For Flash, for any non-English language, and whenever a number matters, write the spoken form yourself:

| Write | as spoken |
|---|---|
| `$42.50` | forty-two dollars and fifty cents |
| `555-555-5555` | five five five, five five five, five five five five |
| `2nd`, `XIV` | second, fourteen |
| `3.5`, `⅔` | three point five, two-thirds |
| `Dr.`, `Ave.` | Doctor, Avenue |
| `100km`, `100%` | one hundred kilometers, one hundred percent |
| `elevenlabs.io/docs` | eleven labs dot io slash docs |
| `2024-01-01`, `14:30` | January first, two thousand twenty-four; two thirty PM |

For automated pipelines either ask an LLM to rewrite the script into fully spoken form (cover currency, phone numbers, ordinals, roman numerals, decimals and fractions, abbreviations, units, symbols, URLs, dates, times, addresses), or preprocess with regex plus a number-to-words library (`inflect` in Python, `number-to-words` in TypeScript).

## 5. Multi-speaker dialogue
- Text to Dialogue API (v4 recommended, v3 supported): an `inputs` array of `{text, voice_id}` objects; no limit on speakers; keep the total at or below 2,000 characters per request.
- Give every speaker a clearly different voice, put tags inside each line, use dashes and ellipses for interruptions and hesitation, set `seed` for reproducibility, and generate several versions to choose from.

## 6. Production workflow (proven on the Mirror pitch and teasers)
1. **Script file first.** One line per segment: `S01|[tag] text …`. Keep each segment well under the model's character limit (a slide or paragraph, ~20–60 s of speech).
2. **Plain copy for alignment.** Keep a second version with all `[tags]` removed; forced alignment and STT checks need the exact spoken text.
3. **Generate 2–3 takes per segment** (same voice, same settings; v3 stability 0.5 is the safe default). Run the requests in parallel (about 6 at a time) and make the job skip files that already exist, so failed requests (timeouts, SSL drops) can simply be re-run.
4. **QC every take with speech-to-text** (`scribe` STT with the right `language_code`, e.g. `eng`, `fas`): compare to the plain script (word similarity), flag missing words, tag words read aloud (e.g. the voice saying "pause"), long gaps (>2.5 s) and durations far from the median of the takes. Pick the best-scoring take, then listen to the important lines; STT cannot judge tone.
5. **Forced alignment** (`/v1/forced-alignment`) of the picked take with its plain text gives word-level timings for subtitles, word-synced on-screen text and edit points.
6. **Keep every take** with a clear name (`S17_a/b/c`) so a slide can be swapped later without regenerating.
7. **Mix:** loudness-normalize the final mix (−14 LUFS for social and video); keep the voice about 15 dB above the music.

House rules: never print the API key (read it from the key file); ask before starting any new kind of paid generation or a large new batch; audio tags always in English.

## 7. Persian (and other non-English) scripts
- Tags in English, text in Persian. Use spoken register (`می‌شه`, `نگه‌تون داره`) for natural delivery.
- Write numbers, dates, prices and percentages as Persian words (`پانصد و سی و دو`, `ده درصد`).
- Fix a mispronounced word with diacritics on the wrong syllable only (`اِلِوِن‌لَبز` for ElevenLabs, `اِم‌وی‌پی` for MVP), or rewrite the phrase. Keep a per-project pronunciation glossary.
- Use the zero-width non-joiner correctly (`می‌خوام`, `گفت‌وگو`); broken joins change pronunciation.
- STT checks for Persian: normalize ی/ي, ک/ك, ZWNJ and diacritics before comparing; brand names may come back in Latin script.
- For the full Persian writing rules see the `persian-ai-dialogue-writing` skill.

## 8. Pre-flight checklist
- [ ] Model chosen for the job; text under its character limit.
- [ ] Voice suits the delivery; tags match the voice and the line.
- [ ] No SSML break or phoneme tags on v3/v4; pauses done with punctuation, structure or pause tags, and never an ellipsis plus a pause tag in the same spot.
- [ ] Tags short (one word or a short pair), lowercase, one per bracket, no identical tag twice in a row.
- [ ] Numbers, symbols, abbreviations and URLs written as spoken words.
- [ ] Risky names fixed with IPA (v4), alias/dictionary, respelling or diacritics, and tested alone first.
- [ ] Settings set: stability (0.5 to start), seed if reproducibility matters; no speed or style on v4.
- [ ] Plan for 2–3 takes plus STT QC plus alignment; key never printed; paid-generation permission confirmed.