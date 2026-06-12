#!/usr/bin/env python3
"""② 转录：fsmn-vad 切段 + SenseVoiceSmall 逐段识别。

句级时间戳以 VAD 段边界为准（可靠），不使用字级时间戳（SenseVoice 的
CTC 字级对齐有已知的对不齐问题）。

产物（每条视频）：
  transcript/<id>.jsonl       每行 {video_id, seg_id, start_ms, end_ms, text}
  transcript/<id>.srt         播放器用（空文本段不写入）
  transcript/<id>.meta.json   时长 / VAD 语音总时长 / 已转写时长，供 ②′ 校验

断点续跑：每条完成后写 transcript/.done/<id>，重跑自动跳过。
首次运行会从 ModelScope 下载模型（约 1GB）。
"""
import argparse
import json
import time
from pathlib import Path

import soundfile as sf

from common import is_done, mark_done, write_jsonl, write_srt

SAMPLE_RATE = 16000
ASR_BATCH = 16  # 每批送 ASR 的 VAD 段数


def load_models(device: str):
    from funasr import AutoModel

    vad = AutoModel(model="fsmn-vad", device=device, disable_update=True)
    asr = AutoModel(model="iic/SenseVoiceSmall", device=device, disable_update=True)
    return vad, asr


def transcribe_file(wav_path: Path, vad, asr):
    from funasr.utils.postprocess_utils import rich_transcription_postprocess

    audio, sr = sf.read(wav_path, dtype="float32")
    if sr != SAMPLE_RATE:
        raise ValueError(f"{wav_path} 采样率为 {sr}，请先用 01_extract_audio.sh 转成 16kHz")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    vad_res = vad.generate(input=str(wav_path), max_single_segment_time=30000)
    segments = vad_res[0]["value"]  # [[start_ms, end_ms], ...]

    vid = wav_path.stem
    rows = []
    for i in range(0, len(segments), ASR_BATCH):
        batch = segments[i : i + ASR_BATCH]
        clips = [audio[int(s * sr / 1000) : int(e * sr / 1000)] for s, e in batch]
        res = asr.generate(input=clips, fs=SAMPLE_RATE, language="zh", use_itn=True)
        for (s, e), r in zip(batch, res):
            text = rich_transcription_postprocess(r["text"]).strip()
            rows.append(
                {
                    "video_id": vid,
                    "seg_id": len(rows),
                    "start_ms": int(s),
                    "end_ms": int(e),
                    "text": text,
                }
            )

    vad_speech_ms = sum(e - s for s, e in segments)
    transcribed_ms = sum(r["end_ms"] - r["start_ms"] for r in rows if r["text"])
    meta = {
        "video_id": vid,
        "audio_duration_ms": int(len(audio) / sr * 1000),
        "vad_speech_ms": int(vad_speech_ms),
        "transcribed_ms": int(transcribed_ms),
        "n_segments": len(segments),
        "n_empty": sum(1 for r in rows if not r["text"]),
    }
    return rows, meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--audio-dir", default="audio")
    ap.add_argument("--out-dir", default="transcript")
    ap.add_argument("--device", default="cpu", help="默认 cpu；funasr 对 mps 支持不稳，慎用")
    ap.add_argument("--delete-audio", action="store_true", help="转录成功后删除 wav（磁盘紧张时用）")
    args = ap.parse_args()

    audio_dir, out_dir = Path(args.audio_dir), Path(args.out_dir)
    done_dir = out_dir / ".done"
    wavs = sorted(audio_dir.glob("*.wav"))
    if not wavs:
        print(f"{audio_dir} 下没有 wav，先跑 01_extract_audio.sh")
        return

    vad, asr = load_models(args.device)
    for wav in wavs:
        vid = wav.stem
        if is_done(done_dir, vid):
            print(f"skip {vid}（已完成）")
            continue
        t0 = time.time()
        rows, meta = transcribe_file(wav, vad, asr)
        write_jsonl(out_dir / f"{vid}.jsonl", rows)
        write_srt(out_dir / f"{vid}.srt", [r for r in rows if r["text"]])
        (out_dir / f"{vid}.meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        mark_done(done_dir, vid)
        speed = meta["audio_duration_ms"] / 1000 / max(time.time() - t0, 1e-6)
        print(f"done {vid}: {meta['n_segments']} 段, 约 {speed:.0f}x 实时")
        if args.delete_audio:
            wav.unlink()


if __name__ == "__main__":
    main()
