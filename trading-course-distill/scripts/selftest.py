#!/usr/bin/env python3
"""不依赖 funasr/ffmpeg 的自测：用伪造的转录数据跑通 ②′ 校验和 ③ 校正。

用法: python3 scripts/selftest.py
"""
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from common import ms_to_hms, ms_to_timecode, read_jsonl, write_jsonl  # noqa: E402


def fake_video(workdir: Path, vid: str, coverage_ok: bool, monotonic: bool):
    duration = 3 * 3600_000  # 3 小时
    rows, t = [], 0
    for i in range(200):
        start = t
        end = start + 8000
        text = f"这里有一个回采确认的买点 第{i}段" if i % 3 == 0 else f"大家稍等一下 第{i}段"
        rows.append({"video_id": vid, "seg_id": i, "start_ms": start, "end_ms": end, "text": text})
        t = end + 45_000  # 均匀铺满约 3 小时
    if not monotonic:
        rows[50]["start_ms"], rows[51]["start_ms"] = rows[51]["start_ms"], rows[50]["start_ms"]
    transcribed = sum(r["end_ms"] - r["start_ms"] for r in rows)
    vad_speech = transcribed if coverage_ok else int(transcribed / 0.8)  # 0.8 覆盖率 -> 应标红
    tdir = workdir / "transcript"
    write_jsonl(tdir / f"{vid}.jsonl", rows)
    (tdir / f"{vid}.meta.json").write_text(
        json.dumps(
            {
                "video_id": vid,
                "audio_duration_ms": duration,
                "vad_speech_ms": vad_speech,
                "transcribed_ms": transcribed,
                "n_segments": len(rows),
                "n_empty": 0,
            }
        ),
        encoding="utf-8",
    )


def main():
    assert ms_to_timecode(5025_678) == "01:23:45,678"
    assert ms_to_hms(5025_678) == "01:23:45"

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        fake_video(workdir, "good01", coverage_ok=True, monotonic=True)
        fake_video(workdir, "bad02", coverage_ok=False, monotonic=False)
        (workdir / "glossary.csv").write_text(
            "wrong,right,type,note\n回采,回踩,术语,自测用\n", encoding="utf-8"
        )

        for script in ("02b_coverage_check.py", "03_correct_terms.py"):
            r = subprocess.run(
                [sys.executable, str(SCRIPTS / script)], cwd=workdir, capture_output=True, text=True
            )
            assert r.returncode == 0, f"{script} 失败:\n{r.stdout}\n{r.stderr}"

        # ②′ 断言：good01 通过，bad02 被标红
        with open(workdir / "qa/coverage_report.csv", encoding="utf-8") as f:
            report = {r["video_id"]: r for r in csv.DictReader(f)}
        assert report["good01"]["flag"] == "OK", report["good01"]
        assert "LOW_COVERAGE" in report["bad02"]["flag"], report["bad02"]
        assert "NON_MONOTONIC" in report["bad02"]["flag"], report["bad02"]
        spotcheck = (workdir / "qa/tail_spotcheck.md").read_text(encoding="utf-8")
        assert "## good01" in spotcheck and "- [ ] `02:" in spotcheck

        # ③ 断言：替换落盘 + 日志可审计
        clean = read_jsonl(workdir / "clean/good01.jsonl")
        assert any("回踩" in r["text"] for r in clean)
        assert not any("回采" in r["text"] for r in clean)
        with open(workdir / "qa/replace_log/good01.csv", encoding="utf-8") as f:
            log = list(csv.DictReader(f))
        assert log and log[0]["wrong"] == "回采"
        assert (workdir / "clean/good01.srt").exists()

    print("selftest PASS：②′ 覆盖率/单调性/尾部抽查、③ 替换与日志 均符合预期")


if __name__ == "__main__":
    main()
