#!/usr/bin/env bash
# music + whoosh on cuts + hits on the drop / explosion / end card
set -e; S=${SFX:-../../news-reel/sfx}; B=0.48407; P=0.48
bt(){ python3 -c "print(round($P+$1*$B,3))"; }
cuts=($(bt 10) $(bt 18) $(bt 29) $(bt 31) $(bt 35) $(bt 43) $(bt 47) $(bt 53)); hits=($(bt 31) $(bt 53) $(bt 57))
ins=(-i music.mp3); f="[0:a]atrim=0:30.5,afade=t=out:st=29.9:d=0.6,volume=1.0[m];"; n=1; mixin="[m]"
for c in "${cuts[@]}"; do ms=$(python3 -c "print(int(($c-0.15)*1000))"); ins+=(-i $S/whoosh.mp3); f+="[$n:a]volume=0.35,adelay=$ms|$ms[a$n];"; mixin+="[a$n]"; n=$((n+1)); done
for c in "${hits[@]}"; do ms=$(python3 -c "print(int($c*1000))"); ins+=(-i $S/hit.mp3); f+="[$n:a]volume=0.45,adelay=$ms|$ms[a$n];"; mixin+="[a$n]"; n=$((n+1)); done
f+="${mixin}amix=inputs=$n:normalize=0,atrim=0:30.5,loudnorm=I=-12:TP=-1.5:LRA=9,alimiter=limit=0.85:level=false[o]"
ffmpeg -y -loglevel error "${ins[@]}" -filter_complex "$f" -map "[o]" -ar 48000 mix.wav
ffmpeg -y -loglevel error -i out/news.mp4 -i mix.wav -c:v copy -c:a aac -b:a 256k -shortest -movflags +faststart promo.mp4
ffmpeg -hide_banner -i promo.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):" | tail -2
