# LOOP.md · 迭代闭环定义（为 /loop 准备）

本文件定义 `zettaranc-perspective` skill 的自动迭代任务与**闭环（终止）条件**。
供 `/loop` 循环执行时读取，每轮按「执行 → 检查 → 判定」推进，闭环条件满足即停止循环。

## 启动方式

```
/loop 30m 按 .claude/skills/zettaranc-perspective/LOOP.md 执行一轮迭代；若「闭环条件」已全部满足，更新迭代日志后结束loop，不再续期
```

## 每轮迭代任务

1. **质量门禁**：运行
   `python3 .claude/skills/zettaranc-perspective/scripts/quality_check.py .claude/skills/zettaranc-perspective/SKILL.md`
2. **有 FAIL 项** → 按女娲方法论（`.claude/skills/nuwa/SKILL.md` Phase 2/3）修复对应 section，重跑检查
3. **新语料检测**：若 `references/sources/` 出现新素材（直播转写/文章/访谈），先按女娲「更新已有Skill」流程增量更新，再回到步骤1
4. **时效检查**（本skill特有）：zettaranc 是活跃创作者（每周直播），若距「调研时间」超过6个月，标记「建议更新」并在迭代日志注明——但这不阻塞闭环，仅当用户提供新语料或明确要求更新时才执行更新
5. **记录**：将本轮结果追加到「迭代日志」，提交并推送

## 闭环条件（全部满足 → 结束 loop）

| # | 条件 | 判定方式 | 当前状态 |
|---|------|---------|---------|
| 1 | quality_check.py **6/6 PASS**（退出码0） | 机器判定 | ✅ 已满足 |
| 2 | `references/sources/` 无未消化的新语料 | 对比迭代日志 | ✅ 已满足（快速档网络调研，无本地语料） |
| 3 | 迭代次数 ≤ 上限 **2轮**（超限则诚实边界标注薄弱项后交付当前最优版，同样视为闭环） | 数迭代日志行数 | ✅ 第1轮即闭环 |

**闭环后的行为**：更新迭代日志 → 提交推送 → 结束 loop（不再 re-arm / 不再续期）。
**重开条件**：新语料放入 `references/sources/`、用户说「更新Z哥的skill」、或时效检查触发且用户确认更新。

## 迭代日志

| 轮次 | 日期 | quality_check | 处理内容 | 判定 |
|------|------|--------------|---------|------|
| 1 | 2026-07-02 | 6/6 PASS | 初次蒸馏（快速档网络调研+lululu811/zettaranc-skill交叉验证）：5个心智模型 + 10条启发式 + 表达DNA + 4对张力 + 诚实边界 | **闭环 ✅** |

> 当前状态：**已闭环（CLOSED）**。语料调研时间 2026-07-02，按时效规则 2027-01 后建议增量更新。
