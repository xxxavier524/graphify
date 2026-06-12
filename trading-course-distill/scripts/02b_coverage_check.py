#!/usr/bin/env python3
"""②′ 完整性校验：覆盖率、时间戳单调性、尾部漂移抽查清单。

产物：
  qa/coverage_report.csv   每条视频一行，flag 列非 OK 的需要处理
  qa/tail_spotcheck.md     每条视频末 10 分钟抽 3 句，人工对照播放器验时间戳

覆盖率 = 非空字幕时长 / VAD 语音总时长，默认阈值 0.95。
"""
import argparse
import csv
import json
from pathlib import Path

from common import ms_to_hms, read_jsonl

TAIL_WINDOW_MS = 10 * 60_000  # 末 10 分钟
TAIL_SAMPLES = 3


def check_video(jsonl_path: Path, meta_path: Path, threshold: float):
    rows = read_jsonl(jsonl_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    coverage = meta["transcribed_ms"] / meta["vad_speech_ms"] if meta["vad_speech_ms"] else 0.0
    monotonic = all(
        rows[i]["start_ms"] >= rows[i - 1]["start_ms"] for i in range(1, len(rows))
    ) and all(r["end_ms"] > r["start_ms"] for r in rows)

    flags = []
    if coverage < threshold:
        flags.append("LOW_COVERAGE")
    if not monotonic:
        flags.append("NON_MONOTONIC")
    if not rows:
        flags.append("EMPTY")

    report_row = {
        "video_id": meta["video_id"],
        "duration": ms_to_hms(meta["audio_duration_ms"]),
        "vad_speech_min": round(meta["vad_speech_ms"] / 60_000, 1),
        "coverage": round(coverage, 4),
        "n_segments": meta["n_segments"],
        "n_empty": meta["n_empty"],
        "monotonic": monotonic,
        "flag": "|".join(flags) or "OK",
    }

    # 尾部抽查：末 10 分钟内均匀取 3 句非空字幕
    tail_start = meta["audio_duration_ms"] - TAIL_WINDOW_MS
    tail = [r for r in rows if r["start_ms"] >= tail_start and r["text"]]
    if len(tail) > TAIL_SAMPLES:
        step = len(tail) // TAIL_SAMPLES
        tail = [tail[i * step] for i in range(TAIL_SAMPLES)]
    spotcheck = [
        f"- [ ] `{ms_to_hms(r['start_ms'])}` {r['text'][:40]}" for r in tail
    ]
    return report_row, spotcheck


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript-dir", default="transcript")
    ap.add_argument("--qa-dir", default="qa")
    ap.add_argument("--threshold", type=float, default=0.95)
    args = ap.parse_args()

    transcript_dir, qa_dir = Path(args.transcript_dir), Path(args.qa_dir)
    qa_dir.mkdir(parents=True, exist_ok=True)

    reports, spotcheck_md = [], ["# 尾部时间戳抽查清单", "", "在播放器中定位以下时间点，对照字幕内容是否一致（误差应 < 2 秒）：", ""]
    for jsonl_path in sorted(transcript_dir.glob("*.jsonl")):
        meta_path = jsonl_path.parent / f"{jsonl_path.stem}.meta.json"
        if not meta_path.exists():
            print(f"warn: {jsonl_path.stem} 缺 meta.json，跳过")
            continue
        report_row, spotcheck = check_video(jsonl_path, meta_path, args.threshold)
        reports.append(report_row)
        spotcheck_md.append(f"## {report_row['video_id']}")
        spotcheck_md.extend(spotcheck or ["（末 10 分钟无字幕——本身就值得人工看一眼）"])
        spotcheck_md.append("")

    if not reports:
        print("没有可校验的转录结果")
        return

    report_path = qa_dir / "coverage_report.csv"
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(reports[0].keys()))
        writer.writeheader()
        writer.writerows(reports)
    (qa_dir / "tail_spotcheck.md").write_text("\n".join(spotcheck_md), encoding="utf-8")

    bad = [r for r in reports if r["flag"] != "OK"]
    print(f"共 {len(reports)} 条，{len(bad)} 条需处理 -> {report_path}")
    for r in bad:
        print(f"  {r['video_id']}: {r['flag']} (coverage={r['coverage']})")


if __name__ == "__main__":
    main()
