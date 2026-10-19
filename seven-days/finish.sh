#!/usr/bin/env bash
# Mux picture + music/sfx mix (+ optional narration in voice/V*.mp3, ducking the bed), loudness -14 LUFS, true peak -1 dBFS.
# Usage: ./finish.sh out/picture60.mp4 out/mix.wav out/seven-days.mp4
set -euo pipefail
cd "$(dirname "$0")"
pic="$1"; mix="$2"; out="$3"
if ls voice/V*.mp3 >/dev/null 2>&1; then
  inputs=(); filt=""; n=0
  while IFS='|' read -r id slot text; do
    [[ "$id" =~ ^V[0-9]+$ ]] || continue; f="voice/$id.mp3"; [ -f "$f" ] || continue
    bar="${slot%,*}"; beat="${slot#*,}"; ms=$(python3 -c "print(int(round((($bar*4)+$beat)*60/90*1000)))")
    inputs+=(-i "$f"); n=$((n+1)); filt+="[$((n+1)):a]adelay=${ms}|${ms},aformat=channel_layouts=stereo[v$n];"
  done < voice/script.txt
  vl=""; for i in $(seq 1 $n); do vl+="[v$i]"; done
  filt+="${vl}amix=inputs=$n:normalize=0,volume=1.6[vo];[vo]asplit[vo1][vo2];[1:a][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=350[bed];[bed][vo2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.84:level=false[a]"
  ffmpeg -y -loglevel error -i "$pic" -i "$mix" "${inputs[@]}" -filter_complex "$filt" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 256k -shortest "$out"
else
  ffmpeg -y -loglevel error -i "$pic" -i "$mix" -filter_complex "[1:a]loudnorm=I=-14:TP=-1.5:LRA=9,alimiter=limit=0.84:level=false[a]" -map 0:v -map "[a]" -c:v libx264 -preset slow -crf 21 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 256k -shortest "$out"
fi
echo "wrote $out"
