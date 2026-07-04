# LOOP.md · 迭代闭环定义（为 /loop 准备）

本文件定义 `jin-jiancheng-perspective` skill 的自动迭代任务与**闭环（终止）条件**。
供 `/loop` 循环执行时读取，每轮迭代按「执行 → 检查 → 判定」推进，闭环条件满足即停止循环。

## 启动方式

```
/loop 30m 按 .claude/skills/jin-jiancheng-perspective/LOOP.md 执行一轮迭代；若「闭环条件」已全部满足，更新迭代日志后结束loop，不再续期
```

## 每轮迭代任务

1. **质量门禁**：运行
   `python3 .claude/skills/jin-jiancheng-perspective/scripts/quality_check.py .claude/skills/jin-jiancheng-perspective/SKILL.md`
2. **有 FAIL 项** → 按女娲方法论（`.claude/skills/nuwa/SKILL.md` Phase 2/3）修复对应 section，重跑检查
3. **新语料检测**：若 `references/sources/` 出现新素材（新的文章/访谈/导图），先增量更新调研文件与 SKILL.md（女娲「更新已有Skill」流程），再回到步骤1
4. **记录**：将本轮结果追加到下方「迭代日志」，提交并推送

## 闭环条件（全部满足 → 结束 loop）

| # | 条件 | 判定方式 | 当前状态 |
|---|------|---------|---------|
| 1 | quality_check.py **6/6 PASS**（退出码0） | 机器判定 | ✅ 已满足 |
| 2 | `references/sources/` 无未消化的新语料 | 对比迭代日志中已处理素材清单 | ✅ 已满足（仅1份导图，已消化） |
| 3 | 迭代次数 ≤ 上限 **2轮**（女娲Phase 4规则：超限则在诚实边界标注薄弱项后交付当前最优版，同样视为闭环） | 数迭代日志行数 | ✅ 第1轮即闭环 |

**闭环后的行为**：更新迭代日志 → 提交推送 → 结束 loop（不再 re-arm / 不再续期）。
**重开条件**：用户提供新语料放入 `references/sources/`，或用户说「更新金渐成的skill」→ 条件2失效，loop 可重新启动。

## 迭代日志

| 轮次 | 日期 | quality_check | 处理内容 | 判定 |
|------|------|--------------|---------|------|
| 1 | 2026-07-02 | 6/6 PASS | 初次蒸馏：转写导图 → 5个心智模型 + 9条启发式 + 表达DNA + 诚实边界；修复一手来源占比统计 | **闭环 ✅** |

> 当前状态：**已闭环（CLOSED）**。/loop 启动后第一轮即会确认闭环并自行终止；仅当出现新语料时才有实际迭代工作。
