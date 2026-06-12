#!/usr/bin/env python3
"""③ 术语校正（白名单制）。

Pass 1（落盘）：按 glossary.csv 做确定性查找替换 transcript -> clean，
               并写替换日志 qa/replace_log/<id>.csv（可审计、可回滚）。
Pass 2（可选，--mine-candidates）：用本地 LLM（ollama）扫疑似错词，
               仅写 qa/term_candidates.csv 供人工审核入典。LLM 永不直接改稿。

glossary.csv 列：wrong,right,type,note
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from common import read_jsonl, write_jsonl, write_srt


def load_glossary(path: Path):
    with open(path, encoding="utf-8") as f:
        entries = [r for r in csv.DictReader(f) if r.get("wrong") and r.get("right")]
    # 长词优先替换，避免「压力位子」被「位子」类短词截胡
    return sorted(entries, key=lambda r: len(r["wrong"]), reverse=True)


def correct_rows(rows, glossary):
    log = []
    for row in rows:
        text = row["text"]
        for entry in glossary:
            n = text.count(entry["wrong"])
            if n:
                text = text.replace(entry["wrong"], entry["right"])
                log.append(
                    {
                        "video_id": row["video_id"],
                        "seg_id": row["seg_id"],
                        "wrong": entry["wrong"],
                        "right": entry["right"],
                        "count": n,
                    }
                )
        row["text"] = text
    return rows, log


def mine_candidates(rows, model: str, ollama_url: str):
    """LLM 错词候选挖掘骨架：分块送审，输出候选清单，不改稿。"""
    import urllib.request

    prompt_tmpl = (
        "下面是股票直播课的语音转写片段，可能存在同音错别字（尤其是股票名、炒股术语）。\n"
        "找出疑似转错的词，每行输出一条 JSON：{\"wrong\": 错词, \"right\": 猜测的正确词}。\n"
        "没有就输出 NONE。只输出 JSON 行或 NONE，不要解释。\n\n片段：\n{chunk}"
    )
    candidates = Counter()
    suggestions = {}
    texts = [r["text"] for r in rows if r["text"]]
    chunk_size = 30
    for i in range(0, len(texts), chunk_size):
        chunk = "\n".join(texts[i : i + chunk_size])
        payload = json.dumps(
            {"model": model, "prompt": prompt_tmpl.replace("{chunk}", chunk), "stream": False}
        ).encode()
        req = urllib.request.Request(
            f"{ollama_url}/api/generate", data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                answer = json.loads(resp.read())["response"]
        except Exception as e:
            print(f"warn: ollama 调用失败（{e}），跳过本块")
            continue
        for line in answer.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                c = json.loads(line)
                if c.get("wrong"):
                    candidates[c["wrong"]] += 1
                    suggestions[c["wrong"]] = c.get("right", "")
            except json.JSONDecodeError:
                continue
    return candidates, suggestions


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript-dir", default="transcript")
    ap.add_argument("--clean-dir", default="clean")
    ap.add_argument("--qa-dir", default="qa")
    ap.add_argument("--glossary", default="glossary.csv")
    ap.add_argument("--mine-candidates", action="store_true", help="用本地 LLM 挖错词候选（需要 ollama）")
    ap.add_argument("--ollama-model", default="qwen3:8b")
    ap.add_argument("--ollama-url", default="http://localhost:11434")
    args = ap.parse_args()

    transcript_dir, clean_dir, qa_dir = Path(args.transcript_dir), Path(args.clean_dir), Path(args.qa_dir)
    glossary = load_glossary(Path(args.glossary))
    log_dir = qa_dir / "replace_log"
    log_dir.mkdir(parents=True, exist_ok=True)

    all_candidates, all_suggestions = Counter(), {}
    n_videos, n_replaced = 0, 0
    for jsonl_path in sorted(transcript_dir.glob("*.jsonl")):
        rows = read_jsonl(jsonl_path)
        rows, log = correct_rows(rows, glossary)
        vid = jsonl_path.stem
        write_jsonl(clean_dir / f"{vid}.jsonl", rows)
        write_srt(clean_dir / f"{vid}.srt", [r for r in rows if r["text"]])
        if log:
            with open(log_dir / f"{vid}.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["video_id", "seg_id", "wrong", "right", "count"])
                writer.writeheader()
                writer.writerows(log)
        n_videos += 1
        n_replaced += sum(e["count"] for e in log)

        if args.mine_candidates:
            cands, sugg = mine_candidates(rows, args.ollama_model, args.ollama_url)
            all_candidates.update(cands)
            all_suggestions.update(sugg)

    print(f"校正完成：{n_videos} 条视频，替换 {n_replaced} 处 -> {clean_dir}/")

    if args.mine_candidates and all_candidates:
        cand_path = qa_dir / "term_candidates.csv"
        with open(cand_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["candidate", "suggestion", "count"])
            for wrong, n in all_candidates.most_common():
                writer.writerow([wrong, all_suggestions.get(wrong, ""), n])
        print(f"错词候选 {len(all_candidates)} 个 -> {cand_path}（人工审核后手动加入 glossary.csv）")


if __name__ == "__main__":
    main()
