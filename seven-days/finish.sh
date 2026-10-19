#!/usr/bin/env bash
# Mux picture + music/sfx mix (+ optional narration in voice/V*.mp3, ducking the bed), loudness -14 LUFS, true peak -1 dBFS.
# Usage: ./finish.sh out/picture60.mp4 out/mix.wav out/seven-days.mp4
set -euo pipefail
cd "$(dirname "$0")"
pic="$1"; mix="$2"; out="$3"
if [ -f voice/voice.wav ]; then
  ffmpeg -y -loglevel error -i "$pic" -i "$mix" -i voice/voice.wav -filter_complex "[1:a]loudnorm=I=-24:TP=-3:LRA=11[m];[2:a]highpass=f=90,equalizer=f=3200:t=q:w=1.2:g=2.5,acompressor=threshold=0.1:ratio=3:attack=8:release=120:makeup=1.5,loudnorm=I=-16:TP=-2:LRA=7,asplit[v1][v2];[m][v1]sidechaincompress=threshold=0.04:ratio=5:attack=20:release=400[bed];[bed][v2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.84:level=false[a]" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 256k -shortest "$out"
else
  ffmpeg -y -loglevel error -i "$pic" -i "$mix" -filter_complex "[1:a]loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.84:level=false[a]" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 256k -shortest "$out"
fi
echo "wrote $out"
