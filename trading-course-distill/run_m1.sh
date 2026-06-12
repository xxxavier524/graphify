#!/usr/bin/env bash
# M1 端到端：①抽音频 → ②转录 → ②′校验 → ③校正
# 把 1 条视频放进 raw/ 后执行本脚本。
set -euo pipefail
cd "$(dirname "$0")"

./scripts/01_extract_audio.sh raw audio
python3 scripts/02_transcribe.py --audio-dir audio --out-dir transcript
python3 scripts/02b_coverage_check.py
python3 scripts/03_correct_terms.py

echo ""
echo "M1 流水线完成。验收三件事："
echo "  1) qa/coverage_report.csv —— flag 列应全为 OK（覆盖率 >= 0.95）"
echo "  2) qa/tail_spotcheck.md  —— 在播放器中对照末段时间戳，误差应 < 2 秒"
echo "  3) 抽读 clean/<id>.srt   —— 确认文本可用、术语错误已记入 glossary.csv"
