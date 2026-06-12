"""共用工具：done 标记、JSONL 读写、时间码、SRT 生成。"""
import json
from pathlib import Path


def ms_to_timecode(ms: int, sep: str = ",") -> str:
    """毫秒 -> SRT 时间码 HH:MM:SS,mmm"""
    ms = int(ms)
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, milli = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{milli:03d}"


def ms_to_hms(ms: int) -> str:
    """毫秒 -> hh:mm:ss（知识卡片回链用）"""
    return ms_to_timecode(ms).split(",")[0]


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_srt(path, rows):
    """rows: [{start_ms, end_ms, text}, ...] -> SRT"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for i, row in enumerate(rows, 1):
            f.write(
                f"{i}\n"
                f"{ms_to_timecode(row['start_ms'])} --> {ms_to_timecode(row['end_ms'])}\n"
                f"{row['text']}\n\n"
            )


def is_done(done_dir, video_id) -> bool:
    return (Path(done_dir) / video_id).exists()


def mark_done(done_dir, video_id):
    d = Path(done_dir)
    d.mkdir(parents=True, exist_ok=True)
    (d / video_id).touch()
