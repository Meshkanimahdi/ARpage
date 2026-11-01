---
name: reel-audio-mix
description: Mix and master the sound of a meshkani.pro reel so it feels alive, not dry — voice delivery (ElevenLabs settings and audio tags), voice/music/SFX buses, ducking, room, loudness for Instagram. Use for every reel before reel_assemble.py, and when a reel sounds flat, dry, harsh, muddy, too quiet or too loud.
---
# Reel audio: mix and master (user rule 2026-11-02)
Mahdi: «صداهای تولید شده برای ریلزها خیلی خشک و بی‌روحه… مهارت میکس و مسترینگ صدا خیلی مهمه».
There is no ready mixing skill in the catalog, so this is ours. `news-reel/reel_assemble.py` applies the chain
below automatically; this file is how to get the inputs right and how to check the result.

## 1. Delivery (before the mix: a flat read cannot be mixed alive)
- ElevenLabs v3/v4 with **audio tags on most beats** (`[curious]`, `[excited]`, `[whispers]`, `[serious]`,
  `[laughs]`, `[sighs]`, `[short pause]`): the hook beat excited or surprised, the data beat serious, the
  turn whispered or slower, the ending warm. Read skill `skill-elevenlabs-tts` for tag rules.
- `stability` 0.35–0.45 (default now 0.38; 0.5 sounded flat), similarity 0.85, speaker boost on.
- Write for the ear: short sentences, questions, a pause before the number, contrast words («ولی»، «اما»).
- Pick a voice from audio_library.json that fits the mood (husky/deep for serious news, warm/bright for life
  tips), never one of the last 12 reels.

## 2. Buses (done in reel_assemble.py)
| bus | chain | why |
|---|---|---|
| voice | HPF 80 Hz · LPF 15 kHz · −2.5 dB @250 Hz · +3 dB @3.2 kHz · +2 dB shelf @9 kHz · de-ess · comp 3:1 −20 dB · short room (23/41 ms, very low) | removes mud and boom, adds presence and air, kills sibilance, steady level, takes the "dry booth" edge off |
| music | HPF 35 Hz · −4 dB @2.8 kHz · sidechain duck 6:1 from the voice, release 450 ms | carves room for speech; music swells back in pauses |
| SFX | motion-matched cues or one SFX v3 soundscape (RUNBOOK §4.3 3b/3c), ≤ 0.45 each | punctuation, not wallpaper |
| master | glue comp 2:1 −14 dB · loudnorm −14 LUFS, TP −1.5 dB, LRA 9 · limiter 0.8 | Instagram plays at about −14 LUFS; louder only gets turned down and squashed |

## 3. Music choice
- One track per reel from the library, matched to mood and tempo of the edit; not the track of the last 3 reels.
- Start the music under the hook (not silence), drop it for one beat at the turn, bring it back for the end.

## 4. Check by ear and numbers (every reel)
- `reel.json`: −15.5…−12 LUFS (target −14), true peak ≤ −1 dBFS.
- Listen to the first 5 s and the turn: the voice must sit on top, clear on a phone speaker; music audible but
  never fighting the words; no "s" hiss; no sudden loud SFX.
- The critic's `visual_match` note includes the sound: a reel that feels dry or flat is fixed (tags,
  stability, music choice) before publishing when time allows.
