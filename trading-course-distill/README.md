# trading-course-distill · M1 阶段脚本

股票直播课 → 个人交易 Skill 蒸馏的处理流水线。
完整方案见 [`docs/plans/2026-06-12-trading-course-skill-distillation.md`](../docs/plans/2026-06-12-trading-course-skill-distillation.md)。

当前包含 M1（打通）阶段的四个脚本：

| 脚本 | 阶段 | 说明 |
|---|---|---|
| `scripts/01_extract_audio.sh` | ① | 视频 → 16kHz 单声道 wav，幂等可重跑 |
| `scripts/02_transcribe.py` | ② | fsmn-vad 切段 + SenseVoiceSmall 识别，句级时间戳，断点续跑 |
| `scripts/02b_coverage_check.py` | ②′ | 覆盖率 / 单调性校验 + 尾部时间戳抽查清单 |
| `scripts/03_correct_terms.py` | ③ | 词典白名单替换（落盘）+ LLM 错词候选挖掘（仅出清单） |

## 环境准备（Mac mini M4）

```bash
brew install ffmpeg
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

- 首次运行 `02_transcribe.py` 会从 ModelScope 下载模型（SenseVoiceSmall + fsmn-vad，约 1GB）。
- 内存：5 小时音频整段载入约 1.2GB，加模型与运行时总占用约 2–3GB，16G 无压力；
  但**不要与本地 LLM 同时跑**。
- 设备默认 `cpu`（SenseVoice 非自回归，CPU 已是数十倍实时）；funasr 对 `mps` 支持不稳，不建议。

## M1 跑法

```bash
# 0) 先自测纯逻辑部分（不需要 funasr/ffmpeg）
python3 scripts/selftest.py

# 1) 放 1 条视频进 raw/（或软链接：ln -s /path/to/视频.mp4 raw/）
mkdir -p raw

# 2) 端到端
./run_m1.sh
```

产物：

```
transcript/<id>.jsonl|.srt|.meta.json   # 模式A：句级时间戳逐字稿
qa/coverage_report.csv                  # 覆盖率报告（flag 列非 OK 需处理）
qa/tail_spotcheck.md                    # 末段时间戳人工抽查清单
qa/replace_log/<id>.csv                 # 词典替换日志（可审计回滚）
clean/<id>.jsonl|.srt                   # 校正后字幕
```

## M1 验收标准（方案 §7）

- [ ] `qa/tail_spotcheck.md` 中末 10 分钟的时间点在播放器中对照，误差 < 2 秒
- [ ] `qa/coverage_report.csv` 覆盖率 ≥ 0.95，无 NON_MONOTONIC
- [ ] 抽读 `clean/<id>.srt`，文本"可用"，发现的错词已记入 `glossary.csv`

验收通过后进入 M2（5–10 条小批量、集中建词典、标定 ④ 预过滤阈值）。

## 常用参数

```bash
# 磁盘紧张：转录成功后即删 wav
python3 scripts/02_transcribe.py --delete-audio

# 错词候选挖掘（需要本地 ollama，先 ollama pull qwen3:8b）
python3 scripts/03_correct_terms.py --mine-candidates
# 产出 qa/term_candidates.csv，人工审核后手动并入 glossary.csv —— LLM 永不直接改稿
```

## 词典 glossary.csv

格式：`wrong,right,type,note`。当前是示例条目，跑完第一条视频后按实际错词维护。
建议用 akshare 拉一份全 A 股股票名称表做打底（M2 阶段做）。
