# 融合到本地量化选股 agent team

本目录是集成套件：把「Z哥」从静态 skill 变成 agent team 里的一名成员（交易纪律官）。

## 方式一：Claude Code 项目（推荐）

在你本地的 agentteam 项目根目录执行：

```bash
# 1. 拉取 skill 分支（PR 合并后可改用默认分支）
git clone --depth 1 -b claude/github-nuwa-skill-setup-0y0v8v \
  https://github.com/xxxavier524/graphify /tmp/zt-skill

# 2. 安装 skill（思维框架）+ 子代理（团队成员）
mkdir -p .claude/skills .claude/agents
cp -r /tmp/zt-skill/.claude/skills/zettaranc-perspective .claude/skills/
cp .claude/skills/zettaranc-perspective/integration/agents/zettaranc-discipline-officer.md .claude/agents/

rm -rf /tmp/zt-skill
```

装完后两种用法：

| 用法 | 触发方式 | 角色 |
|------|---------|------|
| **Skill**（对话人格） | 对 Claude 说「用Z哥的视角看这个票的买点」 | 交易纪律顾问，你直接和他聊 |
| **Subagent**（团队成员） | 主 agent 在流水线里 spawn `zettaranc-discipline-officer`，把已放行的候选标的交给它 | 交易纪律官：趋势定性→资金确认→B1进场→止损止盈纪律卡 |

## 与金渐成闸门的配合（推荐团队编排）

```
信号生成/回测 agent
      ↓ 候选标的
jin-jiancheng-gatekeeper   （风控闸门：买不买、仓位上限）
      ↓ 放行标的
zettaranc-discipline-officer（纪律官：何时买、止损线、何时无条件离场）
      ↓ 纪律卡
执行/组合构建 agent
```

两人体系互补：金渐成管期望值与生存边界（周期+赔率+边界），Z哥管执行纪律（B1买点+只输一根K线+四块砖）。冲突时以更保守一方为准（两个 agent 定义中均已写入此规则）。

## 方式二：非 Claude Code 框架（AutoGen / LangGraph / CrewAI 等）

1. 把 `SKILL.md` 全文作为纪律官 agent 的 **system prompt**
2. 把 `integration/agents/zettaranc-discipline-officer.md` 正文（去掉 frontmatter）追加为任务指令
3. 编排：`选股信号 → 风控闸门 → Z哥纪律官 → 执行`，纪律官输出机械可执行的纪律卡

## 质量与迭代

- 质量门禁：`python3 scripts/quality_check.py SKILL.md`（当前 6/6 PASS）
- 迭代闭环：见 `LOOP.md`；人物活跃更新中，语料截止 2026-03，建议半年级别增量更新

> ⚠️ 思维框架模拟，不构成投资建议。
