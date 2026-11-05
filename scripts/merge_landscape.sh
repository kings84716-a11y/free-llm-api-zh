#!/usr/bin/env bash
# 用 concat filter 重编码合并所有段（时间戳连续），再混 BGM，避免 AAC 时间戳损坏
set -e
cd /home/ubuntu/free-api-hub/video/build_h
OUT=/home/ubuntu/free-api-hub/video/free-api-ep1-landscape.mp4
BGM=/home/ubuntu/free-api-hub/video/assets/bgm.mp3

# 构造 concat filter 输入参数
inputs=(); labels=""
i=0
for f in card_0.mp4 s0.mp4 s1.mp4 s2.mp4 s3.mp4 s4.mp4 s5.mp4 s6.mp4 s7.mp4 s8.mp4 s9.mp4 card_1.mp4; do
  [ -f "$f" ] || continue
  inputs+=(-i "$f"); labels+="[$i:v][$i:a]"; i=$((i+1))
done
n=$i
# concat 重编码
ffmpeg -y "${inputs[@]}" -filter_complex "${labels}concat=n=${n}:v=1:a=1[v][a]" \
  -map "[v]" -map "[a]" -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 160k clean.mp4 2>/dev/null
echo "clean: $(ffprobe -v error -show_entries format=duration -of csv=p=0 clean.mp4)s"

# 烧字幕（重新用 sub.ass）
ffmpeg -y -i clean.mp4 -vf "ass=sub.ass" -c:a copy subbed2.mp4 2>/dev/null
echo "subbed2: $(ffprobe -v error -show_entries format=duration -of csv=p=0 subbed2.mp4)s"

# 混 BGM
ffmpeg -y -i subbed2.mp4 -stream_loop -1 -i "$BGM" \
  -filter_complex "[1:a]volume=0.12[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 160k "$OUT" 2>/dev/null
echo "FINAL: $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")s"
