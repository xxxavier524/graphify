#!/usr/bin/env bash
# ① 批量抽音频：raw/ 下的视频 -> audio/<id>.wav（16kHz 单声道）
# 用法: ./scripts/01_extract_audio.sh [raw目录] [audio目录]
# 幂等：已存在的 wav 自动跳过；中断后直接重跑即可。
set -euo pipefail

RAW_DIR=${1:-raw}
AUDIO_DIR=${2:-audio}
mkdir -p "$AUDIO_DIR"

shopt -s nullglob nocaseglob
for f in "$RAW_DIR"/*.{mp4,mkv,mov,flv,ts,webm,m4a,avi}; do
  id=$(basename "$f")
  id=${id%.*}
  out="$AUDIO_DIR/$id.wav"
  if [ -s "$out" ]; then
    echo "skip $id（已存在）"
    continue
  fi
  tmp="$AUDIO_DIR/.$id.part.wav"
  ffmpeg -nostdin -hide_banner -loglevel error -i "$f" -vn -ac 1 -ar 16000 -y "$tmp"
  mv "$tmp" "$out"
  echo "done $id"
done
