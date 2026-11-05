#!/usr/bin/env bash
# make_bgm.sh — ffmpeg 合成无版权轻量科技感 BGM（柔和和弦，约64秒）
set -e
OUT="/home/ubuntu/free-api-hub/video/assets/bgm.mp3"
mkdir -p "$(dirname "$OUT")"
ffmpeg -y \
 -f lavfi -i "sine=frequency=261.63:duration=64" \
 -f lavfi -i "sine=frequency=329.63:duration=64" \
 -f lavfi -i "sine=frequency=392.00:duration=64" \
 -f lavfi -i "sine=frequency=196.00:duration=64" \
 -filter_complex "[0:a]volume=0.18[a0];[1:a]volume=0.12[a1];[2:a]volume=0.10[a2];[3:a]volume=0.14[a3];\
[a0][a1][a2][a3]amix=inputs=4:duration=longest:normalize=0,\
tremolo=f=0.3:d=0.3,afade=t=in:st=0:d=2,afade=t=out:st=60:d=4,lowpass=f=2200,volume=0.5" \
 -c:a libmp3lame -b:a 128k "$OUT"
echo "BGM -> $OUT"
ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT"
